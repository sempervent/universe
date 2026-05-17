#pragma once

#include "CoreMinimal.h"
#include "UniverseSignalVisual.generated.h"

/** Per-object appearance driven by the active instrument mode. */
USTRUCT(BlueprintType)
struct FUniverseSignalVisual
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly)
	float Emphasis = 1.f;

	UPROPERTY(BlueprintReadOnly)
	FLinearColor Tint = FLinearColor::White;

	UPROPERTY(BlueprintReadOnly)
	float Opacity = 1.f;

	UPROPERTY(BlueprintReadOnly)
	bool bVisible = true;

	UPROPERTY(BlueprintReadOnly)
	bool bAbstractInference = false;

	UPROPERTY(BlueprintReadOnly)
	float JetEmissiveScale = 1.f;
};
