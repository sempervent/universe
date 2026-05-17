#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "UniverseTelescopeHUD.generated.h"

UCLASS()
class UNIVERSE_API AUniverseTelescopeHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void DrawHUD() override;

protected:
	void DrawPanel(const FString& Title, const TArray<FString>& Lines, float X, float Y) const;
	bool ObjectTypeNeedsVisualizationNote(const FString& Type) const;
	FString VisualizationNoteForType(const FString& Type) const;
};
