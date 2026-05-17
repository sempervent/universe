#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Pawn.h"
#include "UniverseTelescopePawn.generated.h"

class USpringArmComponent;
class UCameraComponent;
class AUniverseSceneActor;

UCLASS()
class UNIVERSE_API AUniverseTelescopePawn : public APawn
{
	GENERATED_BODY()

public:
	AUniverseTelescopePawn();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<USpringArmComponent> SpringArm;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
	TObjectPtr<UCameraComponent> Camera;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe|Camera")
	float OrbitSpeed = 0.35f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe|Camera")
	float ZoomSpeed = 120.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe|Camera")
	float MinArmLength = 80.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Universe|Camera")
	float MaxArmLength = 4000.f;

	UFUNCTION(BlueprintCallable, Category = "Universe|Camera")
	void FocusOnLocation(const FVector& WorldLocation, float FitRadius = 200.f);

	UFUNCTION(BlueprintCallable, Category = "Universe|Camera")
	void FocusSelectedOrRecommended();

	UFUNCTION(BlueprintCallable, Category = "Universe|Camera")
	void ResetTelescopeView();

	UFUNCTION(BlueprintCallable, Category = "Universe|Camera")
	void SelectObjectUnderCursor();

	UFUNCTION(BlueprintCallable, Category = "Universe|Camera")
	AUniverseSceneActor* GetSceneActor() const;

protected:
	virtual void BeginPlay() override;
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;
	virtual void Tick(float DeltaSeconds) override;

	void OrbitYaw(float Value);
	void OrbitPitch(float Value);
	void ZoomArm(float Value);
	void CycleSignalMode();
	void ToggleLabels();
	void CycleFeaturedTarget();

	FVector FocusTarget = FVector::ZeroVector;
	bool bLabelsEnabled = false;

	UFUNCTION()
	void OnSignalModeChanged();
};
