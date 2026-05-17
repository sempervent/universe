#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UniverseSignalVisual.h"
#include "UniverseSignalModeSubsystem.generated.h"

UENUM(BlueprintType)
enum class EUniverseSignalMode : uint8
{
	VisibleLight UMETA(DisplayName = "Visible Light"),
	Radio UMETA(DisplayName = "Radio"),
	Microwave UMETA(DisplayName = "Microwave"),
	XRay UMETA(DisplayName = "X-Ray"),
	GammaRay UMETA(DisplayName = "Gamma Ray"),
	GravitationalWave UMETA(DisplayName = "Gravitational Wave"),
	Neutrino UMETA(DisplayName = "Neutrino"),
	WeakLensing UMETA(DisplayName = "Weak Lensing"),
	DarkMatterInference UMETA(DisplayName = "Dark Matter Inference"),
	SpeculativeNowSignal UMETA(DisplayName = "Speculative Now Signal"),
	Ultraviolet UMETA(DisplayName = "Ultraviolet"),
	Infrared UMETA(DisplayName = "Infrared"),
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnUniverseSignalModeChanged, EUniverseSignalMode, NewMode);

/**
 * Instrument visualization modes — conceptual parity with Godot SkyRenderer.
 */
UCLASS()
class UNIVERSE_API UUniverseSignalModeSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UPROPERTY(BlueprintAssignable, Category = "Universe|Signal")
	FOnUniverseSignalModeChanged OnSignalModeChanged;

	UPROPERTY(BlueprintReadOnly, Category = "Universe|Signal")
	EUniverseSignalMode CurrentMode = EUniverseSignalMode::VisibleLight;

	UFUNCTION(BlueprintCallable, Category = "Universe|Signal")
	void SetMode(EUniverseSignalMode Mode);

	UFUNCTION(BlueprintCallable, Category = "Universe|Signal")
	bool SetModeFromString(const FString& ModeId);

	UFUNCTION(BlueprintCallable, Category = "Universe|Signal")
	void CycleMode();

	UFUNCTION(BlueprintPure, Category = "Universe|Signal")
	FString GetModeIdString() const;

	UFUNCTION(BlueprintPure, Category = "Universe|Signal")
	FString GetHelpText(bool bDeepField) const;

	UFUNCTION(BlueprintPure, Category = "Universe|Signal")
	float GetEmphasisForType(const FString& ObjectType, bool bDeepField) const;

	UFUNCTION(BlueprintPure, Category = "Universe|Signal")
	FUniverseSignalVisual GetVisualForType(const FString& ObjectType, bool bDeepField) const;

	UFUNCTION(BlueprintPure, Category = "Universe|Signal")
	FLinearColor GetModeAmbientTint() const;

	UFUNCTION(BlueprintPure, Category = "Universe|Signal")
	bool IsSpeculativeMode() const;

	static EUniverseSignalMode PrimaryCycleModes[10];
};
