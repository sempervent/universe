#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UniverseSceneTypes.h"
#include "UniverseSceneActor.generated.h"

class UInstancedStaticMeshComponent;
class UStaticMeshComponent;
class AUniverseObjectActor;
class AUniverseFilamentActor;

UCLASS()
class UNIVERSE_API AUniverseSceneActor : public AActor
{
	GENERATED_BODY()

public:
	AUniverseSceneActor();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe|Scene")
	FString SceneJsonPath;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe|Scene")
	bool bPreferUnrealBundle = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe|Scene")
	bool bAutoLoadOnBeginPlay = true;

	UPROPERTY(BlueprintReadOnly, Category = "Universe|Scene")
	FUniverseSceneRegion LoadedScene;

	UPROPERTY(BlueprintReadOnly, Category = "Universe|Scene")
	TObjectPtr<AUniverseObjectActor> SelectedObject;

	UPROPERTY(BlueprintReadOnly, Category = "Universe|Scene")
	int32 FeaturedFocusIndex = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Universe|Scene")
	bool bLabelsEnabled = false;

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	bool LoadAndSpawnScene();

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	void ApplySignalModeToScene();

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	void SelectObject(AUniverseObjectActor* Object);

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	void ClearSelection();

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	bool SelectObjectFromHit(const FHitResult& Hit);

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	void CycleFeaturedTarget();

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	void RefreshLabelVisibility();

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	void ApplySceneMetadataDefaults();

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	AUniverseObjectActor* FindObjectActor(const FString& ObjectId) const;

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	FVector GetRecommendedCameraFocus() const;

	UFUNCTION(BlueprintCallable, Category = "Universe|Scene")
	FVector GetFocusLocation() const;

	UFUNCTION(BlueprintPure, Category = "Universe|Scene")
	FString GetRecommendedTargetLabel() const;

	UPROPERTY(BlueprintReadOnly, Category = "Universe|Scene")
	TArray<TObjectPtr<AUniverseObjectActor>> ObjectActors;

	UPROPERTY(BlueprintReadOnly, Category = "Universe|Scene")
	TArray<TObjectPtr<AUniverseFilamentActor>> FilamentActors;

protected:
	virtual void BeginPlay() override;

	void ClearSpawned();
	void SpawnFromLoadedScene();
	void ApplyGalaxySignalVisual();
	void MarkFeaturedAndRecommended();

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UInstancedStaticMeshComponent> GalaxyInstances;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<UStaticMeshComponent> CmbShell;

	FVector CentroidMpc = FVector::ZeroVector;
	float RenderScale = 1.f;
};
