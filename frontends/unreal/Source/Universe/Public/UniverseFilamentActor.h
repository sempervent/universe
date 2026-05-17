#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UniverseSceneTypes.h"
#include "UniverseFilamentActor.generated.h"

class USplineComponent;
class UStaticMeshComponent;

UCLASS()
class UNIVERSE_API AUniverseFilamentActor : public AActor
{
	GENERATED_BODY()

public:
	AUniverseFilamentActor();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<USplineComponent> Spline;

	UFUNCTION(BlueprintCallable, Category = "Universe")
	void BuildFromPath(const TArray<FVector>& WorldPoints, float TubeRadius = 4.f);

	UFUNCTION(BlueprintCallable, Category = "Universe")
	void ApplySignalVisual(const struct FUniverseSignalVisual& Visual);

protected:
	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> SegmentMeshes;
};
