#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UniverseCosmicMaterials.generated.h"

class UMaterialInstanceDynamic;
class UMaterialInterface;
class UPrimitiveComponent;

/** Material profile — code-side parents from engine stock materials. */
UENUM(BlueprintType)
enum class ECosmicMaterialProfile : uint8
{
	Emissive,
	Translucent,
	Filament,
	BlackHole,
	Cmb,
};

/**
 * Runtime material service (no committed .uasset required).
 *
 * Uses engine stock materials (e.g. BasicShapeMaterial) with MID parameters.
 * Editor-authored M_Cosmic* assets can replace parents later via config.
 */
UCLASS()
class UNIVERSE_API UUniverseCosmicMaterials : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	UFUNCTION(BlueprintCallable, Category = "Universe|Materials")
	UMaterialInstanceDynamic* CreateMIDForProfile(
		ECosmicMaterialProfile Profile,
		UObject* Outer) const;

	UFUNCTION(BlueprintCallable, Category = "Universe|Materials")
	void ApplyToComponent(
		UPrimitiveComponent* Component,
		int32 MaterialSlot,
		ECosmicMaterialProfile Profile,
		FLinearColor BaseColor,
		float EmissiveStrength,
		float Opacity,
		FLinearColor Tint = FLinearColor::White) const;

	UFUNCTION(BlueprintPure, Category = "Universe|Materials")
	bool UsesCodeFallback() const { return true; }

protected:
	UPROPERTY()
	TObjectPtr<UMaterialInterface> EmissiveParent;

	UPROPERTY()
	TObjectPtr<UMaterialInterface> TranslucentParent;

	UPROPERTY()
	TObjectPtr<UMaterialInterface> FilamentParent;

	void ApplyParameterAliases(
		UMaterialInstanceDynamic* Mid,
		FLinearColor Color,
		float EmissiveStrength,
		float Opacity) const;

	UMaterialInterface* ResolveParent(ECosmicMaterialProfile Profile) const;
};
