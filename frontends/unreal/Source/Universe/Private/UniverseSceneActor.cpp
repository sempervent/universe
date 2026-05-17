#include "UniverseSceneActor.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Kismet/GameplayStatics.h"
#include "UniverseCosmicMaterials.h"
#include "UniverseFilamentActor.h"
#include "UniverseObjectActor.h"
#include "UniverseSceneImporter.h"
#include "UniverseSignalModeSubsystem.h"
#include "Universe.h"
#include "UObject/ConstructorHelpers.h"

static TAutoConsoleVariable<FString> CVarUniverseScenePath(
	TEXT("universe.SceneJsonPath"),
	TEXT(""),
	TEXT("Absolute or project-relative path to canonical scene.json"));

AUniverseSceneActor::AUniverseSceneActor()
{
	PrimaryActorTick.bCanEverTick = false;
	SceneJsonPath = UUniverseSceneImporter::DefaultSceneJsonPath();

	GalaxyInstances = CreateDefaultSubobject<UInstancedStaticMeshComponent>(TEXT("GalaxyInstances"));
	GalaxyInstances->SetupAttachment(RootComponent);
	GalaxyInstances->SetCollisionEnabled(ECollisionEnabled::NoCollision);

	CmbShell = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CmbShell"));
	CmbShell->SetupAttachment(RootComponent);
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(
		TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMesh.Succeeded())
	{
		CmbShell->SetStaticMesh(SphereMesh.Object);
		CmbShell->SetWorldScale3D(FVector(48.f));
		CmbShell->SetCastShadow(false);
	}
	CmbShell->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void AUniverseSceneActor::BeginPlay()
{
	Super::BeginPlay();
	if (bAutoLoadOnBeginPlay)
	{
		LoadAndSpawnScene();
	}
}

void AUniverseSceneActor::ClearSpawned()
{
	ClearSelection();
	for (AUniverseObjectActor* Actor : ObjectActors)
	{
		if (Actor)
		{
			Actor->Destroy();
		}
	}
	ObjectActors.Empty();
	for (AUniverseFilamentActor* Fil : FilamentActors)
	{
		if (Fil)
		{
			Fil->Destroy();
		}
	}
	FilamentActors.Empty();
	GalaxyInstances->ClearInstances();
}

bool AUniverseSceneActor::LoadAndSpawnScene()
{
	ClearSpawned();

	const FString CVarPath = CVarUniverseScenePath.GetValueOnGameThread();
	const FString Path = !CVarPath.IsEmpty() ? CVarPath : SceneJsonPath;

	UUniverseSceneImporter* Importer = NewObject<UUniverseSceneImporter>();
	FString Error;
	const bool bOk = bPreferUnrealBundle && Path.Contains(TEXT("scene_unreal.json"))
		? Importer->LoadSceneUnrealBundle(Path, LoadedScene, Error)
		: Importer->LoadSceneFromFile(Path, LoadedScene, Error);

	if (!bOk)
	{
		UE_LOG(LogUniverse, Error, TEXT("%s"), *Error);
		return false;
	}

	UUniverseSceneImporter::ComputeDeepFieldLayout(LoadedScene, CentroidMpc, RenderScale);
	SpawnFromLoadedScene();
	MarkFeaturedAndRecommended();
	ApplySceneMetadataDefaults();
	ApplySignalModeToScene();
	RefreshLabelVisibility();

	UE_LOG(LogUniverse, Log, TEXT("Spawned scene '%s' (%d objects)"),
		*LoadedScene.Name, LoadedScene.Objects.Num());
	return true;
}

void AUniverseSceneActor::SpawnFromLoadedScene()
{
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(
		TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMesh.Succeeded())
	{
		GalaxyInstances->SetStaticMesh(SphereMesh.Object);
	}

	TMap<FString, FCosmicWebNode> NodeMap;
	for (const FCosmicWebNode& Node : LoadedScene.Nodes)
	{
		NodeMap.Add(Node.Id, Node);
	}

	UWorld* World = GetWorld();
	if (!World)
	{
		return;
	}

	for (const FCosmicObject& Obj : LoadedScene.Objects)
	{
		if (Obj.Type == TEXT("cmb_background"))
		{
			continue;
		}

		const FVector WorldPos = UUniverseSceneImporter::PositionMpcToWorld(
			Obj.PositionMpc, LoadedScene, CentroidMpc, RenderScale, LoadedScene.IsSolarSystem());

		if (Obj.Type == TEXT("galaxy"))
		{
			FTransform Xform(FRotator::ZeroRotator, WorldPos, FVector(0.15f));
			GalaxyInstances->AddInstance(Xform);
			continue;
		}

		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AUniverseObjectActor* Actor = World->SpawnActor<AUniverseObjectActor>(
			AUniverseObjectActor::StaticClass(), WorldPos, FRotator::ZeroRotator, Params);
		if (Actor)
		{
			Actor->InitializeFromCosmicObject(Obj, RenderScale);
			ObjectActors.Add(Actor);
		}
	}

	for (const FCosmicWebFilament& Fil : LoadedScene.Filaments)
	{
		TArray<FVector> Path;
		auto AddMpc = [&](const FCosmicVector3& V)
		{
			Path.Add(UUniverseSceneImporter::PositionMpcToWorld(
				V, LoadedScene, CentroidMpc, RenderScale, false));
		};
		if (const FCosmicWebNode* Start = NodeMap.Find(Fil.StartNodeId))
		{
			AddMpc(Start->PositionMpc);
		}
		for (const FCosmicVector3& Cp : Fil.ControlPointsMpc)
		{
			AddMpc(Cp);
		}
		if (const FCosmicWebNode* End = NodeMap.Find(Fil.EndNodeId))
		{
			AddMpc(End->PositionMpc);
		}
		if (Path.Num() < 2)
		{
			continue;
		}

		FActorSpawnParameters Params;
		AUniverseFilamentActor* FilActor = World->SpawnActor<AUniverseFilamentActor>(
			AUniverseFilamentActor::StaticClass(), Path[0], FRotator::ZeroRotator, Params);
		if (FilActor)
		{
			FilActor->BuildFromPath(Path, 4.f);
			FilamentActors.Add(FilActor);
		}
	}

	for (const FCosmicWebNode& Node : LoadedScene.Nodes)
	{
		const FVector WorldPos = UUniverseSceneImporter::PositionMpcToWorld(
			Node.PositionMpc, LoadedScene, CentroidMpc, RenderScale, false);
		FCosmicObject Pseudo;
		Pseudo.Id = Node.Id;
		Pseudo.Name = FString::Printf(TEXT("Node %s"), *Node.Id);
		Pseudo.Type = TEXT("cosmic_web_node");
		Pseudo.PositionMpc = Node.PositionMpc;
		Pseudo.Description = Node.NodeClass;
		FActorSpawnParameters Params;
		AUniverseObjectActor* Actor = World->SpawnActor<AUniverseObjectActor>(
			AUniverseObjectActor::StaticClass(), WorldPos, FRotator::ZeroRotator, Params);
		if (Actor)
		{
			Actor->InitializeFromCosmicObject(Pseudo, (0.42f + Node.Density * 0.22f) * RenderScale);
			ObjectActors.Add(Actor);
		}
	}
}

void AUniverseSceneActor::MarkFeaturedAndRecommended()
{
	const FString RecId = LoadedScene.Metadata.RecommendedCameraTargetObjectId;
	for (AUniverseObjectActor* Actor : ObjectActors)
	{
		if (!Actor)
		{
			continue;
		}
		Actor->bIsFeatured = LoadedScene.Metadata.FeaturedObjectIds.Contains(Actor->ObjectId);
		Actor->bIsRecommendedTarget = Actor->ObjectId == RecId;
	}
	FeaturedFocusIndex = 0;
}

void AUniverseSceneActor::ApplySceneMetadataDefaults()
{
	UGameInstance* GI = GetGameInstance();
	if (!GI)
	{
		return;
	}
	if (UUniverseSignalModeSubsystem* Sig = GI->GetSubsystem<UUniverseSignalModeSubsystem>())
	{
		if (!LoadedScene.Metadata.RecommendedInitialSignalMode.IsEmpty())
		{
			Sig->SetModeFromString(LoadedScene.Metadata.RecommendedInitialSignalMode);
		}
	}
}

void AUniverseSceneActor::ApplySignalModeToScene()
{
	UGameInstance* GI = GetGameInstance();
	UUniverseSignalModeSubsystem* Sig = GI ? GI->GetSubsystem<UUniverseSignalModeSubsystem>() : nullptr;
	if (!Sig)
	{
		return;
	}

	const bool bDeep = LoadedScene.IsDeepField();

	for (AUniverseObjectActor* Actor : ObjectActors)
	{
		if (Actor)
		{
			Actor->ApplySignalVisual(Sig->GetVisualForType(Actor->ObjectType, bDeep));
		}
	}

	const FUniverseSignalVisual FilVis = Sig->GetVisualForType(TEXT("cosmic_web_filament"), bDeep);
	for (AUniverseFilamentActor* Fil : FilamentActors)
	{
		if (Fil)
		{
			Fil->ApplySignalVisual(FilVis);
		}
	}

	ApplyGalaxySignalVisual();

	const FUniverseSignalVisual CmbVis = Sig->GetVisualForType(TEXT("cmb_background"), bDeep);
	if (CmbShell)
	{
		CmbShell->SetVisibility(CmbVis.bVisible && CmbVis.Emphasis > 0.05f);
		if (UGameInstance* GI2 = GetGameInstance())
		{
			if (UUniverseCosmicMaterials* Mats = GI2->GetSubsystem<UUniverseCosmicMaterials>())
			{
				Mats->ApplyToComponent(
					CmbShell, 0, ECosmicMaterialProfile::Cmb,
					FLinearColor(0.12f, 0.04f, 0.06f),
					CmbVis.Emphasis * 0.5f,
					CmbVis.Opacity,
					CmbVis.Tint);
			}
		}
	}

}

void AUniverseSceneActor::ApplyGalaxySignalVisual()
{
	UGameInstance* GI = GetGameInstance();
	UUniverseSignalModeSubsystem* Sig = GI ? GI->GetSubsystem<UUniverseSignalModeSubsystem>() : nullptr;
	if (!Sig)
	{
		return;
	}
	const FUniverseSignalVisual Vis = Sig->GetVisualForType(TEXT("galaxy"), LoadedScene.IsDeepField());
	GalaxyInstances->SetVisibility(Vis.bVisible && Vis.Emphasis > 0.05f, true);

	if (UUniverseCosmicMaterials* Mats = GI->GetSubsystem<UUniverseCosmicMaterials>())
	{
		Mats->ApplyToComponent(
			GalaxyInstances, 0, ECosmicMaterialProfile::Emissive,
			FLinearColor(0.45f, 0.55f, 1.f), Vis.Emphasis * 0.6f, Vis.Opacity, Vis.Tint);
	}
}

void AUniverseSceneActor::SelectObject(AUniverseObjectActor* Object)
{
	if (SelectedObject == Object)
	{
		return;
	}
	if (SelectedObject)
	{
		SelectedObject->SetSelected(false);
	}
	SelectedObject = Object;
	if (SelectedObject)
	{
		SelectedObject->SetSelected(true);
	}
	RefreshLabelVisibility();
}

void AUniverseSceneActor::ClearSelection()
{
	if (SelectedObject)
	{
		SelectedObject->SetSelected(false);
		SelectedObject = nullptr;
	}
	RefreshLabelVisibility();
}

bool AUniverseSceneActor::SelectObjectFromHit(const FHitResult& Hit)
{
	AUniverseObjectActor* HitActor = Cast<AUniverseObjectActor>(Hit.GetActor());
	if (HitActor && ObjectActors.Contains(HitActor))
	{
		SelectObject(HitActor);
		return true;
	}
	return false;
}

void AUniverseSceneActor::CycleFeaturedTarget()
{
	TArray<FString> Ids = LoadedScene.Metadata.FeaturedObjectIds;
	if (Ids.Num() == 0)
	{
		for (AUniverseObjectActor* Actor : ObjectActors)
		{
			if (Actor && Actor->ObjectType == TEXT("lyman_alpha_blob"))
			{
				SelectObject(Actor);
				return;
			}
		}
		return;
	}

	FeaturedFocusIndex = (FeaturedFocusIndex + 1) % Ids.Num();
	if (AUniverseObjectActor* Actor = FindObjectActor(Ids[FeaturedFocusIndex]))
	{
		SelectObject(Actor);
	}
}

void AUniverseSceneActor::RefreshLabelVisibility()
{
	for (AUniverseObjectActor* Actor : ObjectActors)
	{
		if (!Actor)
		{
			continue;
		}
		const bool bShow = bLabelsEnabled
			? (Actor->bIsFeatured || Actor->bIsRecommendedTarget || Actor == SelectedObject)
			: (Actor == SelectedObject || Actor->bIsRecommendedTarget);
		Actor->SetLabelVisible(bShow);
	}
}

AUniverseObjectActor* AUniverseSceneActor::FindObjectActor(const FString& ObjectId) const
{
	for (AUniverseObjectActor* Actor : ObjectActors)
	{
		if (Actor && Actor->ObjectId == ObjectId)
		{
			return Actor;
		}
	}
	return nullptr;
}

FVector AUniverseSceneActor::GetRecommendedCameraFocus() const
{
	const FString TargetId = LoadedScene.Metadata.RecommendedCameraTargetObjectId;
	if (!TargetId.IsEmpty())
	{
		if (const AUniverseObjectActor* Actor = FindObjectActor(TargetId))
		{
			return Actor->GetActorLocation();
		}
	}
	for (const FCosmicObject& Obj : LoadedScene.Objects)
	{
		if (Obj.Type == TEXT("lyman_alpha_blob"))
		{
			return UUniverseSceneImporter::PositionMpcToWorld(
				Obj.PositionMpc, LoadedScene, CentroidMpc, RenderScale, false);
		}
	}
	return FVector::ZeroVector;
}

FVector AUniverseSceneActor::GetFocusLocation() const
{
	if (SelectedObject)
	{
		return SelectedObject->GetActorLocation();
	}
	return GetRecommendedCameraFocus();
}

FString AUniverseSceneActor::GetRecommendedTargetLabel() const
{
	const FString TargetId = LoadedScene.Metadata.RecommendedCameraTargetObjectId;
	if (TargetId.IsEmpty())
	{
		return TEXT("(none)");
	}
	if (const AUniverseObjectActor* Actor = FindObjectActor(TargetId))
	{
		return FString::Printf(TEXT("%s (%s)"), *Actor->DisplayName, *Actor->ObjectType);
	}
	return TargetId;
}
