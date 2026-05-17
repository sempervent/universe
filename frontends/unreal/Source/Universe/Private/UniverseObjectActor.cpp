#include "UniverseObjectActor.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "Engine/StaticMesh.h"
#include "UniverseCosmicMaterials.h"
#include "UObject/ConstructorHelpers.h"

AUniverseObjectActor::AUniverseObjectActor()
{
	PrimaryActorTick.bCanEverTick = true;

	CoreMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("CoreMesh"));
	SetRootComponent(CoreMesh);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(
		TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMesh.Succeeded())
	{
		CoreMesh->SetStaticMesh(SphereMesh.Object);
	}

	CoreLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("CoreLight"));
	CoreLight->SetupAttachment(CoreMesh);
	CoreLight->SetIntensity(0.f);
	CoreLight->SetAttenuationRadius(800.f);

	LabelComponent = CreateDefaultSubobject<UTextRenderComponent>(TEXT("Label"));
	LabelComponent->SetupAttachment(CoreMesh);
	LabelComponent->SetHorizontalAlignment(EHTA_Center);
	LabelComponent->SetWorldSize(28.f);
	LabelComponent->SetRelativeLocation(FVector(0.f, 0.f, 120.f));
	LabelComponent->SetVisibility(false);

	SetupPickCollision(CoreMesh);
	PickableMeshes.Add(CoreMesh);
}

void AUniverseObjectActor::BeginPlay()
{
	Super::BeginPlay();
}

void AUniverseObjectActor::SetupPickCollision(UPrimitiveComponent* Component) const
{
	if (!Component)
	{
		return;
	}
	Component->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	Component->SetCollisionResponseToAllChannels(ECR_Ignore);
	Component->SetCollisionResponseToChannel(ECC_Visibility, ECR_Block);
}

void AUniverseObjectActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bPulse || bSelected)
	{
		return;
	}
	PulsePhase += DeltaSeconds * 2.2f;
	const float Pulse = 0.55f + 0.45f * FMath::Sin(PulsePhase);
	for (FMeshMaterialSlot& Slot : MaterialSlots)
	{
		if (!Slot.Mesh)
		{
			continue;
		}
		float Emissive = BaseEmissive * CachedVisual.Emphasis * Pulse;
		if (Slot.bIsJet)
		{
			Emissive *= CachedVisual.JetEmissiveScale;
		}
		ApplyMaterialToMesh(
			Slot.Mesh,
			Slot.Profile,
			Slot.BaseColor,
			Emissive,
			CachedVisual.Opacity,
			CachedVisual.Tint);
	}
}

FLinearColor AUniverseObjectActor::BaseColorForType(const FString& Type) const
{
	if (Type == TEXT("lyman_alpha_blob")) return FLinearColor(0.2f, 1.f, 0.7f);
	if (Type == TEXT("quasar")) return FLinearColor(1.f, 0.95f, 0.85f);
	if (Type == TEXT("black_hole")) return FLinearColor(0.02f, 0.02f, 0.04f);
	if (Type == TEXT("magnetar")) return FLinearColor(1.f, 0.3f, 1.f);
	if (Type == TEXT("galaxy")) return FLinearColor(0.45f, 0.55f, 1.f);
	if (Type == TEXT("void")) return FLinearColor(0.1f, 0.1f, 0.18f);
	if (Type == TEXT("cosmic_web_node")) return FLinearColor(1.f, 0.55f, 0.25f);
	return FLinearColor(0.6f, 0.6f, 0.65f);
}

ECosmicMaterialProfile AUniverseObjectActor::ProfileForType(const FString& Type) const
{
	if (Type == TEXT("lyman_alpha_blob") || Type == TEXT("void"))
	{
		return ECosmicMaterialProfile::Translucent;
	}
	if (Type == TEXT("black_hole"))
	{
		return ECosmicMaterialProfile::BlackHole;
	}
	return ECosmicMaterialProfile::Emissive;
}

void AUniverseObjectActor::ApplyMaterialToMesh(
	UStaticMeshComponent* Mesh,
	ECosmicMaterialProfile Profile,
	FLinearColor BaseColor,
	float Emissive,
	float Opacity,
	FLinearColor Tint)
{
	if (!Mesh)
	{
		return;
	}
	UGameInstance* GI = GetGameInstance();
	if (!GI)
	{
		return;
	}
	UUniverseCosmicMaterials* Mats = GI->GetSubsystem<UUniverseCosmicMaterials>();
	if (Mats)
	{
		Mats->ApplyToComponent(Mesh, 0, Profile, BaseColor, Emissive, Opacity, Tint);
	}
}

void AUniverseObjectActor::InitializeFromCosmicObject(const FCosmicObject& Object, float BaseScale)
{
	ObjectId = Object.Id;
	ObjectType = Object.Type;
	DisplayName = Object.Name;
	ObjectDescription = Object.Description;
	Relationships = Object.Relationships;

	const FLinearColor Col = BaseColorForType(Object.Type);
	const ECosmicMaterialProfile Profile = ProfileForType(Object.Type);
	BaseEmissive = Object.Visual.bEmissive ? 1.2f : 0.4f;

	float Radius = 30.f * Object.Visual.Scale * BaseScale;
	if (Object.Type == TEXT("lyman_alpha_blob")) Radius = 90.f * BaseScale;
	else if (Object.Type == TEXT("quasar")) Radius = 35.f * BaseScale;
	else if (Object.Type == TEXT("black_hole")) Radius = 28.f * BaseScale;
	else if (Object.Type == TEXT("magnetar")) Radius = 18.f * BaseScale;
	else if (Object.Type == TEXT("galaxy")) Radius = 8.f * BaseScale;
	else if (Object.Type == TEXT("void")) Radius = 120.f * BaseScale;
	else if (Object.Type == TEXT("cosmic_web_node")) Radius = 40.f * BaseScale;

	CoreBaseScale = FVector(Radius / 50.f);
	CoreMesh->SetRelativeScale3D(CoreBaseScale);

	FMeshMaterialSlot CoreSlot;
	CoreSlot.Mesh = CoreMesh;
	CoreSlot.Profile = Profile;
	CoreSlot.BaseColor = Col;
	MaterialSlots.Add(CoreSlot);
	ApplyMaterialToMesh(CoreMesh, Profile, Col, BaseEmissive, Object.Visual.Opacity, FLinearColor::White);

	BuildTypeSpecificVisuals(Object, BaseScale);
	LabelComponent->SetText(FText::FromString(DisplayName));
	SetActorHiddenInGame(false);
}

void AUniverseObjectActor::BuildTypeSpecificVisuals(const FCosmicObject& Object, float BaseScale)
{
	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(
		TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(
		TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> TorusMesh(
		TEXT("/Engine/BasicShapes/Torus.Torus"));

	const FLinearColor Col = BaseColorForType(Object.Type);

	if (Object.Type == TEXT("lyman_alpha_blob"))
	{
		bPulse = true;
		StoredPulseEmissive = 0.65f;
		const float Radii[] = {0.95f, 0.75f, 0.58f};
		const float Alphas[] = {0.35f, 0.25f, 0.18f};
		for (int32 i = 0; i < 3; ++i)
		{
			UStaticMeshComponent* Shell = NewObject<UStaticMeshComponent>(this);
			Shell->SetupAttachment(RootComponent);
			if (SphereMesh.Succeeded())
			{
				Shell->SetStaticMesh(SphereMesh.Object);
			}
			Shell->SetRelativeScale3D(CoreBaseScale * Radii[i]);
			Shell->RegisterComponent();
			SetupPickCollision(Shell);
			PickableMeshes.Add(Shell);
			ExtraMeshes.Add(Shell);

			FMeshMaterialSlot Slot;
			Slot.Mesh = Shell;
			Slot.Profile = ECosmicMaterialProfile::Translucent;
			Slot.BaseColor = Col;
			MaterialSlots.Add(Slot);
			ApplyMaterialToMesh(Shell, ECosmicMaterialProfile::Translucent, Col, 0.55f + i * 0.12f, Alphas[i]);
		}
	}
	else if (Object.Type == TEXT("quasar"))
	{
		CoreLight->SetIntensity(120000.f);
		CoreLight->SetLightColor(Col);
		if (CylinderMesh.Succeeded())
		{
			const int32 JetSigns[] = {1, -1};
			const uint32 Hash = GetTypeHash(Object.Id);
			FVector JetDir(
				static_cast<float>((Hash % 97) / 48.5f - 1.f),
				static_cast<float>(((Hash / 97) % 97) / 48.5f - 1.f),
				static_cast<float>(((Hash / (97 * 97)) % 97) / 48.5f - 1.f));
			if (JetDir.IsNearlyZero())
			{
				JetDir = FVector(0.15f, 1.f, 0.08f);
			}
			JetDir.Normalize();
			for (int32 Sign : JetSigns)
			{
				UStaticMeshComponent* Jet = NewObject<UStaticMeshComponent>(this);
				Jet->SetupAttachment(RootComponent);
				Jet->SetStaticMesh(CylinderMesh.Object);
				Jet->SetRelativeScale3D(FVector(0.08f, 0.08f, 1.4f));
				const FVector Dir = JetDir * static_cast<float>(Sign);
				Jet->SetWorldRotation(Dir.Rotation());
				Jet->SetRelativeLocation(Dir * 70.f);
				Jet->RegisterComponent();
				ExtraMeshes.Add(Jet);

				FMeshMaterialSlot Slot;
				Slot.Mesh = Jet;
				Slot.Profile = ECosmicMaterialProfile::Emissive;
				Slot.BaseColor = Col;
				Slot.bIsJet = true;
				MaterialSlots.Add(Slot);
				ApplyMaterialToMesh(Jet, ECosmicMaterialProfile::Emissive, Col, 2.f, 1.f);
			}
		}
	}
	else if (Object.Type == TEXT("black_hole"))
	{
		if (TorusMesh.Succeeded())
		{
			UStaticMeshComponent* Ring = NewObject<UStaticMeshComponent>(this);
			Ring->SetupAttachment(RootComponent);
			Ring->SetStaticMesh(TorusMesh.Object);
			Ring->SetRelativeScale3D(FVector(1.4f, 1.4f, 0.35f));
			Ring->SetRelativeRotation(FRotator(72.f, 12.f, 0.f));
			Ring->RegisterComponent();
			SetupPickCollision(Ring);
			PickableMeshes.Add(Ring);
			ExtraMeshes.Add(Ring);

			FMeshMaterialSlot Slot;
			Slot.Mesh = Ring;
			Slot.Profile = ECosmicMaterialProfile::BlackHole;
			Slot.BaseColor = FLinearColor(1.f, 0.5f, 0.15f);
			MaterialSlots.Add(Slot);
			ApplyMaterialToMesh(Ring, ECosmicMaterialProfile::BlackHole, Slot.BaseColor, 0.9f, 0.85f);
		}
	}
	else if (Object.Type == TEXT("magnetar"))
	{
		bPulse = true;
		StoredPulseEmissive = 1.1f;
		if (TorusMesh.Succeeded())
		{
			for (float Yaw : {0.f, 120.f})
			{
				UStaticMeshComponent* Field = NewObject<UStaticMeshComponent>(this);
				Field->SetupAttachment(RootComponent);
				Field->SetStaticMesh(TorusMesh.Object);
				Field->SetRelativeScale3D(FVector(1.1f, 1.1f, 0.2f));
				Field->SetRelativeRotation(FRotator(55.f, Yaw, 10.f));
				Field->RegisterComponent();
				ExtraMeshes.Add(Field);

				FMeshMaterialSlot Slot;
				Slot.Mesh = Field;
				Slot.Profile = ECosmicMaterialProfile::Translucent;
				Slot.BaseColor = Col;
				MaterialSlots.Add(Slot);
				ApplyMaterialToMesh(Field, ECosmicMaterialProfile::Translucent, Col, 0.35f, 0.22f);
			}
		}
	}
}

void AUniverseObjectActor::ApplySignalVisual(const FUniverseSignalVisual& Visual)
{
	CachedVisual = Visual;
	const bool bShow = Visual.bVisible && Visual.Emphasis > 0.04f;
	SetActorHiddenInGame(!bShow);

	for (FMeshMaterialSlot& Slot : MaterialSlots)
	{
		if (!Slot.Mesh)
		{
			continue;
		}
		float Emissive = BaseEmissive * Visual.Emphasis;
		if (Slot.bIsJet)
		{
			Emissive *= Visual.JetEmissiveScale;
		}
		if (ObjectType == TEXT("black_hole") && Slot.Profile == ECosmicMaterialProfile::BlackHole)
		{
			Emissive = 0.15f + Visual.Emphasis * 2.f;
		}
		ApplyMaterialToMesh(
			Slot.Mesh,
			Slot.Profile,
			Slot.BaseColor,
			Emissive,
			Visual.Opacity,
			Visual.Tint);
	}

	if (ObjectType == TEXT("quasar"))
	{
		CoreLight->SetIntensity(bShow ? 120000.f * Visual.Emphasis : 0.f);
		CoreLight->SetLightColor(Visual.Tint * BaseColorForType(ObjectType));
	}
}

void AUniverseObjectActor::SetSelected(bool bSelected)
{
	if (this->bSelected == bSelected)
	{
		return;
	}
	this->bSelected = bSelected;

	CoreMesh->SetRelativeScale3D(bSelected ? CoreBaseScale * 1.15f : CoreBaseScale);
	for (UPrimitiveComponent* Mesh : PickableMeshes)
	{
		if (Mesh)
		{
			Mesh->SetRenderCustomDepth(bSelected);
			Mesh->SetCustomDepthStencilValue(bSelected ? 252 : 0);
		}
	}
	SetLabelVisible(bSelected || ShouldShowLabelByDefault());
}

void AUniverseObjectActor::SetLabelVisible(bool bVisible)
{
	LabelComponent->SetVisibility(bVisible);
}

bool AUniverseObjectActor::ShouldShowLabelByDefault() const
{
	return bIsFeatured || bIsRecommendedTarget;
}
