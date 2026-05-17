#include "UniverseFilamentActor.h"
#include "Components/SplineComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "UniverseCosmicMaterials.h"
#include "UniverseSignalVisual.h"
#include "UObject/ConstructorHelpers.h"

AUniverseFilamentActor::AUniverseFilamentActor()
{
	PrimaryActorTick.bCanEverTick = false;
	Spline = CreateDefaultSubobject<USplineComponent>(TEXT("Spline"));
	SetRootComponent(Spline);
}

void AUniverseFilamentActor::BuildFromPath(const TArray<FVector>& WorldPoints, float TubeRadius)
{
	Spline->ClearSplinePoints(false);
	for (const FVector& P : WorldPoints)
	{
		Spline->AddSplinePoint(P, ESplineCoordinateSpace::World, false);
	}
	Spline->UpdateSpline();

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CylinderMesh(
		TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (!CylinderMesh.Succeeded() || WorldPoints.Num() < 2)
	{
		return;
	}

	for (int32 i = 0; i < WorldPoints.Num() - 1; ++i)
	{
		const FVector A = WorldPoints[i];
		const FVector B = WorldPoints[i + 1];
		const float Len = FVector::Distance(A, B);
		if (Len < 1e-3f)
		{
			continue;
		}

		UStaticMeshComponent* Seg = NewObject<UStaticMeshComponent>(this);
		Seg->SetupAttachment(RootComponent);
		Seg->SetStaticMesh(CylinderMesh.Object);
		const FVector Dir = (B - A).GetSafeNormal();
		Seg->SetWorldLocation((A + B) * 0.5f);
		Seg->SetWorldRotation(Dir.Rotation());
		Seg->SetWorldScale3D(FVector(TubeRadius / 50.f, TubeRadius / 50.f, Len / 100.f));
		Seg->RegisterComponent();

		if (UGameInstance* GI = GetGameInstance())
		{
			if (UUniverseCosmicMaterials* Mats = GI->GetSubsystem<UUniverseCosmicMaterials>())
			{
				Mats->ApplyToComponent(
					Seg, 0, ECosmicMaterialProfile::Filament,
					FLinearColor(0.6f, 0.4f, 0.7f), 0.35f, 0.55f);
			}
		}
		SegmentMeshes.Add(Seg);
	}
}

void AUniverseFilamentActor::ApplySignalVisual(const FUniverseSignalVisual& Visual)
{
	const bool bShow = Visual.bVisible && Visual.Emphasis > 0.05f;
	SetActorHiddenInGame(!bShow);
	for (UStaticMeshComponent* Seg : SegmentMeshes)
	{
		if (!Seg)
		{
			continue;
		}
		if (UGameInstance* GI = GetGameInstance())
		{
			if (UUniverseCosmicMaterials* Mats = GI->GetSubsystem<UUniverseCosmicMaterials>())
			{
				Mats->ApplyToComponent(
					Seg, 0, ECosmicMaterialProfile::Filament,
					FLinearColor(0.6f, 0.4f, 0.7f),
					0.12f + Visual.Emphasis * 1.85f,
					0.18f + Visual.Opacity * 0.5f,
					Visual.Tint);
			}
		}
	}
}
