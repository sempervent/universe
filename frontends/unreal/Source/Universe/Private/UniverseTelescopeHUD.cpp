#include "UniverseTelescopeHUD.h"
#include "Engine/Canvas.h"
#include "Kismet/GameplayStatics.h"
#include "UniverseObjectActor.h"
#include "UniverseSceneActor.h"
#include "UniverseSceneTypes.h"
#include "UniverseSignalModeSubsystem.h"

void AUniverseTelescopeHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas)
	{
		return;
	}

	AUniverseSceneActor* Scene = nullptr;
	TArray<AActor*> Scenes;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), AUniverseSceneActor::StaticClass(), Scenes);
	if (Scenes.Num() > 0)
	{
		Scene = Cast<AUniverseSceneActor>(Scenes[0]);
	}

	FString SceneName = TEXT("(no scene loaded)");
	FString SceneClass = TEXT("?");
	float Redshift = 0.f;
	float SizeMpc = 0.f;
	FString Teaching;
	FString RecommendedTarget = TEXT("(none)");
	FString FeaturedLine = TEXT("");
	FString SelectedName = TEXT("(none)");
	FString SelectedType;
	FString SelectedDesc;
	TArray<FString> RelationLines;

	if (Scene)
	{
		SceneName = Scene->LoadedScene.Name;
		SceneClass = Scene->LoadedScene.IsDeepField()
			? TEXT("Deep Field / High-z protocluster")
			: TEXT("Solar System (tutorial)");
		Redshift = Scene->LoadedScene.Redshift;
		SizeMpc = Scene->LoadedScene.SizeMpc;
		Teaching = Scene->LoadedScene.Metadata.TeachingSummary;
		RecommendedTarget = Scene->GetRecommendedTargetLabel();

		if (Scene->LoadedScene.Metadata.FeaturedObjectIds.Num() > 0)
		{
			FeaturedLine = FString::Printf(
				TEXT("Featured [%d/%d]: Tab to cycle"),
				Scene->FeaturedFocusIndex + 1,
				Scene->LoadedScene.Metadata.FeaturedObjectIds.Num());
		}

		if (Scene->SelectedObject)
		{
			SelectedName = Scene->SelectedObject->DisplayName;
			SelectedType = Scene->SelectedObject->ObjectType;
			SelectedDesc = Scene->SelectedObject->ObjectDescription;
			for (const FCosmicRelationship& Rel : Scene->SelectedObject->Relationships)
			{
				RelationLines.Add(FString::Printf(
					TEXT("  %s -> %s"), *Rel.Relation, *Rel.TargetId));
			}
		}
	}

	FString ModeStr = TEXT("visible_light");
	FString Help = TEXT("Instrument view");
	bool bSpec = false;
	if (UGameInstance* GI = GetGameInstance())
	{
		if (UUniverseSignalModeSubsystem* Sig = GI->GetSubsystem<UUniverseSignalModeSubsystem>())
		{
			ModeStr = Sig->GetModeIdString();
			const bool bDeep = Scene && Scene->LoadedScene.IsDeepField();
			Help = Sig->GetHelpText(bDeep);
			bSpec = Sig->IsSpeculativeMode();
		}
	}

	TArray<FString> Header;
	Header.Add(FString::Printf(TEXT("Scene: %s"), *SceneName));
	Header.Add(FString::Printf(TEXT("Kind: %s"), *SceneClass));
	if (Redshift > 1e-4f)
	{
		Header.Add(FString::Printf(TEXT("z ~ %.3f"), Redshift));
	}
	if (SizeMpc > 1e-3f)
	{
		Header.Add(FString::Printf(TEXT("region ~ %.1f cMpc"), SizeMpc));
	}
	Header.Add(FString::Printf(TEXT("Signal: %s%s"), *ModeStr, bSpec ? TEXT(" [SPECULATIVE]") : TEXT("")));
	DrawPanel(TEXT("Universe Telescope"), Header, 24.f, 24.f);

	TArray<FString> Detail;
	Detail.Add(FString::Printf(TEXT("Recommended: %s"), *RecommendedTarget));
	if (!FeaturedLine.IsEmpty())
	{
		Detail.Add(FeaturedLine);
	}
	Detail.Add(FString::Printf(TEXT("Selected: %s"), *SelectedName));
	if (!SelectedType.IsEmpty())
	{
		Detail.Add(FString::Printf(TEXT("Type: %s"), *SelectedType));
	}
	if (!SelectedDesc.IsEmpty())
	{
		Detail.Add(SelectedDesc.Left(160));
	}
	if (ObjectTypeNeedsVisualizationNote(SelectedType))
	{
		Detail.Add(VisualizationNoteForType(SelectedType));
	}
	for (const FString& Rel : RelationLines)
	{
		Detail.Add(Rel);
	}
	if (!Teaching.IsEmpty() && !Scene->SelectedObject)
	{
		Detail.Add(Teaching.Left(140));
	}
	Detail.Add(Help.Left(200));
	DrawPanel(TEXT("Inspector"), Detail, 24.f, 200.f);

	TArray<FString> Keys;
	Keys.Add(TEXT("LMB drag: orbit  |  Wheel: zoom  |  Click: select"));
	Keys.Add(TEXT("M: cycle signal  |  F: focus selected/recommended"));
	Keys.Add(TEXT("R: reset camera  |  N: toggle labels  |  Tab: cycle featured"));
	DrawPanel(TEXT("Controls"), Keys, 24.f, Canvas->SizeY - 100.f);
}

bool AUniverseTelescopeHUD::ObjectTypeNeedsVisualizationNote(const FString& Type) const
{
	return Type == TEXT("lyman_alpha_blob") || Type == TEXT("black_hole");
}

FString AUniverseTelescopeHUD::VisualizationNoteForType(const FString& Type) const
{
	if (Type == TEXT("lyman_alpha_blob"))
	{
		return TEXT("LAB: false-color volume placeholder, not radiative transfer.");
	}
	if (Type == TEXT("black_hole"))
	{
		return TEXT("BH: indirect detection via accretion/lensing metaphors.");
	}
	return TEXT("");
}

void AUniverseTelescopeHUD::DrawPanel(
	const FString& Title,
	const TArray<FString>& Lines,
	float X,
	float Y) const
{
	const float W = 480.f;
	const float H = 28.f + Lines.Num() * 16.f;
	DrawRect(FLinearColor(0.02f, 0.03f, 0.06f, 0.82f), X, Y, W, H);
	DrawText(Title, FLinearColor(0.75f, 0.88f, 1.f), X + 8.f, Y + 4.f, GEngine->GetMediumFont(), 1.f, false);
	float Ly = Y + 24.f;
	for (const FString& Line : Lines)
	{
		DrawText(Line, FLinearColor(0.7f, 0.78f, 0.9f), X + 8.f, Ly, GEngine->GetSmallFont(), 0.9f, false);
		Ly += 16.f;
	}
}
