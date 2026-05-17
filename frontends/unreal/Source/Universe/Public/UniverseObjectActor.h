#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UniverseSceneTypes.h"
#include "UniverseSignalVisual.h"
#include "UniverseObjectActor.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UTextRenderComponent;
class UMaterialInstanceDynamic;
class UUniverseCosmicMaterials;

UCLASS()
class UNIVERSE_API AUniverseObjectActor : public AActor
{
	GENERATED_BODY()

public:
	AUniverseObjectActor();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UStaticMeshComponent> CoreMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UPointLightComponent> CoreLight;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UTextRenderComponent> LabelComponent;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe")
	FString ObjectId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe")
	FString ObjectType;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe")
	FString DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe")
	FString ObjectDescription;

	UPROPERTY(BlueprintReadOnly, Category = "Universe")
	TArray<FCosmicRelationship> Relationships;

	UPROPERTY(BlueprintReadOnly, Category = "Universe")
	bool bIsFeatured = false;

	UPROPERTY(BlueprintReadOnly, Category = "Universe")
	bool bIsRecommendedTarget = false;

	UFUNCTION(BlueprintCallable, Category = "Universe")
	void InitializeFromCosmicObject(const FCosmicObject& Object, float BaseScale = 1.f);

	UFUNCTION(BlueprintCallable, Category = "Universe")
	void ApplySignalVisual(const FUniverseSignalVisual& Visual);

	UFUNCTION(BlueprintCallable, Category = "Universe")
	void SetSelected(bool bSelected);

	UFUNCTION(BlueprintCallable, Category = "Universe")
	void SetLabelVisible(bool bVisible);

	UFUNCTION(BlueprintPure, Category = "Universe")
	bool ShouldShowLabelByDefault() const;

protected:
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	void BuildTypeSpecificVisuals(const FCosmicObject& Object, float BaseScale);
	FLinearColor BaseColorForType(const FString& Type) const;
	ECosmicMaterialProfile ProfileForType(const FString& Type) const;
	void SetupPickCollision(UPrimitiveComponent* Component) const;
	void ApplyMaterialToMesh(
		UStaticMeshComponent* Mesh,
		ECosmicMaterialProfile Profile,
		FLinearColor BaseColor,
		float Emissive,
		float Opacity,
		FLinearColor Tint);

	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> PickableMeshes;

	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> ExtraMeshes;

	struct FMeshMaterialSlot
	{
		TObjectPtr<UStaticMeshComponent> Mesh;
		ECosmicMaterialProfile Profile = ECosmicMaterialProfile::Emissive;
		FLinearColor BaseColor = FLinearColor::White;
		bool bIsJet = false;
	};

	TArray<FMeshMaterialSlot> MaterialSlots;

	FVector CoreBaseScale = FVector::OneVector;
	float BaseEmissive = 0.4f;
	bool bPulse = false;
	bool bSelected = false;
	float PulsePhase = 0.f;
	float StoredPulseEmissive = 0.55f;
	FUniverseSignalVisual CachedVisual;
};
