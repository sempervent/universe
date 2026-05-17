#pragma once

#include "CoreMinimal.h"
#include "UniverseSceneTypes.generated.h"

USTRUCT(BlueprintType)
struct FCosmicVector3
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float X = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Y = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Z = 0.f;

	FVector ToFVector() const { return FVector(X, Y, Z); }

	static FCosmicVector3 FromJson(const TSharedPtr<FJsonObject>& Obj);
};

USTRUCT(BlueprintType)
struct FCosmicVisualHints
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Color;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	bool bEmissive = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Opacity = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Scale = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	bool bGlow = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Label;

	static FCosmicVisualHints FromJson(const TSharedPtr<FJsonObject>& Obj);
};

USTRUCT(BlueprintType)
struct FCosmicRelationship
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString TargetId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Relation;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Description;

	static FCosmicRelationship FromJson(const TSharedPtr<FJsonObject>& Obj);
};

USTRUCT(BlueprintType)
struct FCosmicObject
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Type;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FCosmicVector3 PositionMpc;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Redshift = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Description;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FCosmicVisualHints Visual;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	TArray<FCosmicRelationship> Relationships;

	static FCosmicObject FromJson(const TSharedPtr<FJsonObject>& Obj);
};

USTRUCT(BlueprintType)
struct FCosmicWebNode
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FCosmicVector3 PositionMpc;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Density = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString NodeClass;

	static FCosmicWebNode FromJson(const TSharedPtr<FJsonObject>& Obj);
};

USTRUCT(BlueprintType)
struct FCosmicWebFilament
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString StartNodeId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString EndNodeId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	TArray<FCosmicVector3> ControlPointsMpc;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Density = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float RadiusMpc = 0.5f;

	static FCosmicWebFilament FromJson(const TSharedPtr<FJsonObject>& Obj);
};

USTRUCT(BlueprintType)
struct FUniverseSceneMetadata
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString SceneClass;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString RecommendedCameraTargetObjectId;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString RecommendedInitialSignalMode;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	TArray<FString> FeaturedObjectIds;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString TeachingSummary;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString ScaleDescription;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Description;

	static FUniverseSceneMetadata FromJson(const TSharedPtr<FJsonObject>& Obj);
};

USTRUCT(BlueprintType)
struct FUniverseSceneRegion
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Name;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FString Seed;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float Redshift = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	float SizeMpc = 80.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	FUniverseSceneMetadata Metadata;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	TArray<FCosmicObject> Objects;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	TArray<FCosmicWebNode> Nodes;

	UPROPERTY(EditAnywhere, BlueprintReadWrite)
	TArray<FCosmicWebFilament> Filaments;

	bool IsDeepField() const;
	bool IsSolarSystem() const;

	static bool ParseFromJsonString(const FString& JsonText, FUniverseSceneRegion& OutScene, FString& OutError);
};
