#include "UniverseCosmicMaterials.h"
#include "Materials/Material.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Components/PrimitiveComponent.h"
#include "Universe.h"

void UUniverseCosmicMaterials::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	EmissiveParent = LoadObject<UMaterialInterface>(
		nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	TranslucentParent = LoadObject<UMaterialInterface>(
		nullptr, TEXT("/Engine/EngineMaterials/DefaultParticleMaterial.DefaultParticleMaterial"));
	FilamentParent = EmissiveParent;

	if (!EmissiveParent)
	{
		EmissiveParent = UMaterial::GetDefaultMaterial(MD_Surface);
		UE_LOG(LogUniverse, Warning, TEXT("BasicShapeMaterial not found; using default surface material."));
	}
	if (!TranslucentParent)
	{
		TranslucentParent = EmissiveParent;
	}
	if (!FilamentParent)
	{
		FilamentParent = EmissiveParent;
	}
}

UMaterialInterface* UUniverseCosmicMaterials::ResolveParent(ECosmicMaterialProfile Profile) const
{
	switch (Profile)
	{
	case ECosmicMaterialProfile::Translucent:
		return TranslucentParent ? TranslucentParent.Get() : EmissiveParent.Get();
	case ECosmicMaterialProfile::Filament:
		return FilamentParent ? FilamentParent.Get() : EmissiveParent.Get();
	case ECosmicMaterialProfile::BlackHole:
	case ECosmicMaterialProfile::Emissive:
	case ECosmicMaterialProfile::Cmb:
	default:
		return EmissiveParent.Get();
	}
}

void UUniverseCosmicMaterials::ApplyParameterAliases(
	UMaterialInstanceDynamic* Mid,
	FLinearColor Color,
	float EmissiveStrength,
	float Opacity) const
{
	if (!Mid)
	{
		return;
	}

	const FLinearColor Bright = Color * (1.f + EmissiveStrength * 4.f);
	Bright.A = Opacity;

	Mid->SetVectorParameterValue(TEXT("Color"), Bright);
	Mid->SetVectorParameterValue(TEXT("BaseColor"), Bright);
	Mid->SetVectorParameterValue(TEXT("Tint"), Bright);
	Mid->SetVectorParameterValue(TEXT("EmissiveColor"), Bright * (0.5f + EmissiveStrength));
	Mid->SetScalarParameterValue(TEXT("EmissiveStrength"), EmissiveStrength);
	Mid->SetScalarParameterValue(TEXT("Opacity"), Opacity);
	Mid->SetScalarParameterValue(TEXT("OpacityMask"), Opacity);
}

UMaterialInstanceDynamic* UUniverseCosmicMaterials::CreateMIDForProfile(
	ECosmicMaterialProfile Profile,
	UObject* Outer) const
{
	UMaterialInterface* Parent = ResolveParent(Profile);
	if (!Parent || !Outer)
	{
		return nullptr;
	}
	return UMaterialInstanceDynamic::Create(Parent, Outer);
}

void UUniverseCosmicMaterials::ApplyToComponent(
	UPrimitiveComponent* Component,
	int32 MaterialSlot,
	ECosmicMaterialProfile Profile,
	FLinearColor BaseColor,
	float EmissiveStrength,
	float Opacity,
	FLinearColor Tint) const
{
	if (!Component)
	{
		return;
	}

	UMaterialInstanceDynamic* Mid = CreateMIDForProfile(Profile, Component);
	if (!Mid)
	{
		return;
	}

	const FLinearColor Combined(
		BaseColor.R * Tint.R,
		BaseColor.G * Tint.G,
		BaseColor.B * Tint.B,
		BaseColor.A * Tint.A * Opacity);
	ApplyParameterAliases(Mid, Combined, EmissiveStrength, Opacity);
	Component->SetMaterial(MaterialSlot, Mid);
}
