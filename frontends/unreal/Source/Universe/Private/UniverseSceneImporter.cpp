#include "UniverseSceneImporter.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Universe.h"

FString UUniverseSceneImporter::DefaultSceneJsonPath()
{
	// frontends/unreal -> repo root -> data/generated/scene-001/scene.json
	const FString ProjectDir = FPaths::ConvertRelativePathToFull(FPaths::ProjectDir());
	const FString RepoRelative = FPaths::Combine(ProjectDir, TEXT("../../../data/generated/scene-001/scene.json"));
	return FPaths::ConvertRelativePathToFull(RepoRelative);
}

bool UUniverseSceneImporter::LoadSceneFromFile(
	const FString& AbsoluteOrRelativePath,
	FUniverseSceneRegion& OutScene,
	FString& OutError)
{
	FString Resolved = AbsoluteOrRelativePath;
	if (!FPaths::FileExists(Resolved))
	{
		Resolved = FPaths::ConvertRelativePathToFull(AbsoluteOrRelativePath);
	}
	if (!FPaths::FileExists(Resolved))
	{
		OutError = FString::Printf(TEXT("Scene file not found: %s"), *AbsoluteOrRelativePath);
		return false;
	}

	FString JsonText;
	if (!FFileHelper::LoadFileToString(JsonText, *Resolved))
	{
		OutError = FString::Printf(TEXT("Could not read: %s"), *Resolved);
		return false;
	}

	UE_LOG(LogUniverse, Log, TEXT("Loading scene from %s"), *Resolved);
	return FUniverseSceneRegion::ParseFromJsonString(JsonText, OutScene, OutError);
}

bool UUniverseSceneImporter::LoadSceneUnrealBundle(
	const FString& AbsoluteOrRelativePath,
	FUniverseSceneRegion& OutScene,
	FString& OutError)
{
	FString Resolved = AbsoluteOrRelativePath;
	if (!FPaths::FileExists(Resolved))
	{
		Resolved = FPaths::ConvertRelativePathToFull(AbsoluteOrRelativePath);
	}
	FString JsonText;
	if (!FFileHelper::LoadFileToString(JsonText, *Resolved))
	{
		OutError = TEXT("Could not read unreal bundle");
		return false;
	}

	TSharedPtr<FJsonObject> Root;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
	if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
	{
		OutError = TEXT("Invalid unreal bundle JSON");
		return false;
	}

	const TSharedPtr<FJsonObject>* SceneObj = nullptr;
	if (!Root->TryGetObjectField(TEXT("scene"), SceneObj))
	{
		OutError = TEXT("Bundle missing scene object");
		return false;
	}

	// Re-serialize inner scene to reuse canonical parser (subset fields).
	FString InnerJson;
	const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&InnerJson);
	FJsonSerializer::Serialize((*SceneObj).ToSharedRef(), Writer);
	return FUniverseSceneRegion::ParseFromJsonString(InnerJson, OutScene, OutError);
}

void UUniverseSceneImporter::ComputeDeepFieldLayout(
	const FUniverseSceneRegion& Scene,
	FVector& OutCentroidMpc,
	float& OutRenderScale)
{
	TArray<FVector> Samples;
	if (Scene.Metadata.FeaturedObjectIds.Num() > 0)
	{
		for (const FCosmicObject& Obj : Scene.Objects)
		{
			if (Scene.Metadata.FeaturedObjectIds.Contains(Obj.Id))
			{
				Samples.Add(Obj.PositionMpc.ToFVector());
			}
		}
	}
	if (Samples.Num() == 0)
	{
		for (const FCosmicObject& Obj : Scene.Objects)
		{
			if (Obj.Type == TEXT("lyman_alpha_blob") || Obj.Type == TEXT("quasar") || Obj.Type == TEXT("black_hole"))
			{
				Samples.Add(Obj.PositionMpc.ToFVector());
			}
		}
	}
	if (Samples.Num() == 0 && Scene.Objects.Num() > 0)
	{
		Samples.Add(Scene.Objects[0].PositionMpc.ToFVector());
	}

	FVector Sum = FVector::ZeroVector;
	for (const FVector& S : Samples)
	{
		Sum += S;
	}
	OutCentroidMpc = Samples.Num() > 0 ? Sum / static_cast<float>(Samples.Num()) : FVector::ZeroVector;
	OutRenderScale = 32.f / FMath::Max(Scene.SizeMpc, 1e-3f);
}

FVector UUniverseSceneImporter::PositionMpcToWorld(
	const FCosmicVector3& PositionMpc,
	const FUniverseSceneRegion& Scene,
	const FVector& CentroidMpc,
	float RenderScale,
	bool bSolarLogRadial)
{
	const FVector Mpc = PositionMpc.ToFVector();
	if (Scene.IsSolarSystem() || bSolarLogRadial)
	{
		const float AuToMpc = 4.848e-12f;
		const float AuX = Mpc.X / AuToMpc;
		const float AuZ = Mpc.Z / AuToMpc;
		const float R = FMath::Sqrt(AuX * AuX + AuZ * AuZ);
		if (R < 1e-6f)
		{
			return FVector::ZeroVector;
		}
		const float Compressed = FMath::Loge(1.f + R) * 1.5f;
		const float Scale = Compressed / R;
		return FVector(AuX * Scale, Mpc.Y, AuZ * Scale);
	}

	const FVector Rel = (Mpc - CentroidMpc) * RenderScale;
	// Unreal: X forward, Y right, Z up — keep same axis order as data for now.
	return Rel;
}
