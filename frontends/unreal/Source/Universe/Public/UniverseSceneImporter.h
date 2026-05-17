#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "UniverseSceneTypes.h"
#include "UniverseSceneImporter.generated.h"

/**
 * Loads canonical scene.json (or optional scene_unreal.json convenience bundle).
 */
UCLASS(BlueprintType)
class UNIVERSE_API UUniverseSceneImporter : public UObject
{
	GENERATED_BODY()

public:
	/** Default repo-relative path from frontends/unreal/ to Scene 001 export. */
	static FString DefaultSceneJsonPath();

	UFUNCTION(BlueprintCallable, Category = "Universe|Import")
	bool LoadSceneFromFile(const FString& AbsoluteOrRelativePath, FUniverseSceneRegion& OutScene, FString& OutError);

	UFUNCTION(BlueprintCallable, Category = "Universe|Import")
	bool LoadSceneUnrealBundle(const FString& AbsoluteOrRelativePath, FUniverseSceneRegion& OutScene, FString& OutError);

	/** Deep-field layout: centroid + render scale (matches Godot). */
	UFUNCTION(BlueprintCallable, Category = "Universe|Import")
	static void ComputeDeepFieldLayout(
		const FUniverseSceneRegion& Scene,
		FVector& OutCentroidMpc,
		float& OutRenderScale);

	UFUNCTION(BlueprintCallable, Category = "Universe|Import")
	static FVector PositionMpcToWorld(
		const FCosmicVector3& PositionMpc,
		const FUniverseSceneRegion& Scene,
		const FVector& CentroidMpc,
		float RenderScale,
		bool bSolarLogRadial = false);
};
