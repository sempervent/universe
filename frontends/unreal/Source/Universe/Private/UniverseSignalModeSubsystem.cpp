#include "UniverseSignalModeSubsystem.h"

EUniverseSignalMode UUniverseSignalModeSubsystem::PrimaryCycleModes[10] = {
	EUniverseSignalMode::VisibleLight,
	EUniverseSignalMode::Radio,
	EUniverseSignalMode::Microwave,
	EUniverseSignalMode::XRay,
	EUniverseSignalMode::GammaRay,
	EUniverseSignalMode::GravitationalWave,
	EUniverseSignalMode::Neutrino,
	EUniverseSignalMode::WeakLensing,
	EUniverseSignalMode::DarkMatterInference,
	EUniverseSignalMode::SpeculativeNowSignal,
};

void UUniverseSignalModeSubsystem::SetMode(EUniverseSignalMode Mode)
{
	CurrentMode = Mode;
	OnSignalModeChanged.Broadcast(CurrentMode);
}

bool UUniverseSignalModeSubsystem::SetModeFromString(const FString& ModeId)
{
	const FString Id = ModeId.ToLower();
	if (Id == TEXT("visible_light")) { SetMode(EUniverseSignalMode::VisibleLight); return true; }
	if (Id == TEXT("radio")) { SetMode(EUniverseSignalMode::Radio); return true; }
	if (Id == TEXT("microwave")) { SetMode(EUniverseSignalMode::Microwave); return true; }
	if (Id == TEXT("xray")) { SetMode(EUniverseSignalMode::XRay); return true; }
	if (Id == TEXT("gamma_ray")) { SetMode(EUniverseSignalMode::GammaRay); return true; }
	if (Id == TEXT("gravitational_wave")) { SetMode(EUniverseSignalMode::GravitationalWave); return true; }
	if (Id == TEXT("neutrino")) { SetMode(EUniverseSignalMode::Neutrino); return true; }
	if (Id == TEXT("weak_lensing")) { SetMode(EUniverseSignalMode::WeakLensing); return true; }
	if (Id == TEXT("dark_matter_inference")) { SetMode(EUniverseSignalMode::DarkMatterInference); return true; }
	if (Id == TEXT("speculative_now_signal")) { SetMode(EUniverseSignalMode::SpeculativeNowSignal); return true; }
	if (Id == TEXT("ultraviolet")) { SetMode(EUniverseSignalMode::Ultraviolet); return true; }
	if (Id == TEXT("infrared")) { SetMode(EUniverseSignalMode::Infrared); return true; }
	return false;
}

void UUniverseSignalModeSubsystem::CycleMode()
{
	int32 Idx = 0;
	for (int32 i = 0; i < 10; ++i)
	{
		if (PrimaryCycleModes[i] == CurrentMode)
		{
			Idx = (i + 1) % 10;
			break;
		}
	}
	SetMode(PrimaryCycleModes[Idx]);
}

FString UUniverseSignalModeSubsystem::GetModeIdString() const
{
	switch (CurrentMode)
	{
	case EUniverseSignalMode::VisibleLight: return TEXT("visible_light");
	case EUniverseSignalMode::Radio: return TEXT("radio");
	case EUniverseSignalMode::Microwave: return TEXT("microwave");
	case EUniverseSignalMode::XRay: return TEXT("xray");
	case EUniverseSignalMode::GammaRay: return TEXT("gamma_ray");
	case EUniverseSignalMode::GravitationalWave: return TEXT("gravitational_wave");
	case EUniverseSignalMode::Neutrino: return TEXT("neutrino");
	case EUniverseSignalMode::WeakLensing: return TEXT("weak_lensing");
	case EUniverseSignalMode::DarkMatterInference: return TEXT("dark_matter_inference");
	case EUniverseSignalMode::SpeculativeNowSignal: return TEXT("speculative_now_signal");
	case EUniverseSignalMode::Ultraviolet: return TEXT("ultraviolet");
	case EUniverseSignalMode::Infrared: return TEXT("infrared");
	default: return TEXT("visible_light");
	}
}

FString UUniverseSignalModeSubsystem::GetHelpText(bool bDeepField) const
{
	if (CurrentMode == EUniverseSignalMode::SpeculativeNowSignal)
	{
		return TEXT("FICTIONAL / SPECULATIVE — causality-violating \"now\" view. Not physically meaningful.");
	}
	if (!bDeepField)
	{
		return TEXT("Solar-system tutorial emphasis: bright planets and resolved disks.");
	}
	switch (CurrentMode)
	{
	case EUniverseSignalMode::VisibleLight:
		return TEXT("Optical: galaxies and quasar cores bright; LAB false-color; filaments faint.");
	case EUniverseSignalMode::Radio:
		return TEXT("Radio: quasar jets and magnetar strong; CMB moderate; galaxies dim.");
	case EUniverseSignalMode::Microwave:
		return TEXT("Microwave: CMB shell dominant; discrete sources intentionally dimmed.");
	case EUniverseSignalMode::XRay:
		return TEXT("X-ray: quasar core, accretion ring, magnetar emphasized.");
	case EUniverseSignalMode::GammaRay:
		return TEXT("Gamma-ray: compact high-energy sources emphasized.");
	case EUniverseSignalMode::GravitationalWave:
		return TEXT("GW inference (abstract): compact-object tracers only — not visual light.");
	case EUniverseSignalMode::Neutrino:
		return TEXT("Neutrino inference (abstract): high-energy compact candidates.");
	case EUniverseSignalMode::WeakLensing:
		return TEXT("Weak lensing: filaments, nodes, voids, galaxy distribution as mass tracers.");
	case EUniverseSignalMode::DarkMatterInference:
		return TEXT("Dark-matter map: filaments/nodes/voids strongest; luminous galaxies suppressed.");
	case EUniverseSignalMode::Ultraviolet:
		return TEXT("UV / Lyman-line: LAB volume strongly emphasized.");
	case EUniverseSignalMode::Infrared:
		return TEXT("IR: dusty galaxies and quasar hosts slightly favored.");
	default:
		return TEXT("Instrument visualization (prototype).");
	}
}

FLinearColor UUniverseSignalModeSubsystem::GetModeAmbientTint() const
{
	switch (CurrentMode)
	{
	case EUniverseSignalMode::Radio:
		return FLinearColor(0.35f, 0.22f, 0.45f);
	case EUniverseSignalMode::Microwave:
		return FLinearColor(0.45f, 0.25f, 0.35f);
	case EUniverseSignalMode::XRay:
	case EUniverseSignalMode::GammaRay:
		return FLinearColor(0.2f, 0.35f, 0.55f);
	case EUniverseSignalMode::GravitationalWave:
		return FLinearColor(0.25f, 0.3f, 0.5f);
	case EUniverseSignalMode::Neutrino:
		return FLinearColor(0.22f, 0.38f, 0.42f);
	case EUniverseSignalMode::WeakLensing:
	case EUniverseSignalMode::DarkMatterInference:
		return FLinearColor(0.28f, 0.32f, 0.48f);
	case EUniverseSignalMode::SpeculativeNowSignal:
		return FLinearColor(0.5f, 0.2f, 0.45f);
	case EUniverseSignalMode::Ultraviolet:
		return FLinearColor(0.25f, 0.45f, 0.55f);
	default:
		return FLinearColor(0.25f, 0.3f, 0.42f);
	}
}

float UUniverseSignalModeSubsystem::GetEmphasisForType(const FString& ObjectType, bool bDeepField) const
{
	return GetVisualForType(ObjectType, bDeepField).Emphasis;
}

FUniverseSignalVisual UUniverseSignalModeSubsystem::GetVisualForType(
	const FString& ObjectType,
	bool bDeepField) const
{
	FUniverseSignalVisual V;
	V.Tint = FLinearColor::White;
	V.Opacity = 1.f;
	V.bVisible = true;
	V.JetEmissiveScale = 1.f;

	if (!bDeepField)
	{
		V.Emphasis = 1.f;
		if (CurrentMode == EUniverseSignalMode::SpeculativeNowSignal)
		{
			V.Emphasis = ObjectType.Contains(TEXT("quasar")) ? 0.9f : 0.2f;
			V.Tint = FLinearColor(0.9f, 0.5f, 1.f);
		}
		return V;
	}

	auto Set = [&](float E, FLinearColor Tint, float Opacity, bool bAbstract = false, float Jet = 1.f)
	{
		V.Emphasis = FMath::Clamp(E, 0.04f, 1.f);
		V.Tint = Tint;
		V.Opacity = Opacity;
		V.bAbstractInference = bAbstract;
		V.JetEmissiveScale = Jet;
		V.bVisible = V.Emphasis > 0.05f;
	};

	switch (CurrentMode)
	{
	case EUniverseSignalMode::VisibleLight:
		if (ObjectType == TEXT("galaxy") || ObjectType == TEXT("quasar"))
			Set(1.f, FLinearColor::White, 1.f);
		else if (ObjectType == TEXT("lyman_alpha_blob"))
			Set(0.48f, FLinearColor(0.3f, 1.f, 0.75f), 0.35f);
		else if (ObjectType == TEXT("black_hole"))
			Set(0.1f, FLinearColor(0.02f, 0.02f, 0.04f), 0.25f);
		else if (ObjectType == TEXT("magnetar"))
			Set(0.55f, FLinearColor::White, 0.9f);
		else if (ObjectType == TEXT("cosmic_web_filament"))
			Set(0.22f, FLinearColor(0.5f, 0.4f, 0.65f), 0.35f);
		else if (ObjectType == TEXT("cosmic_web_node") || ObjectType == TEXT("void"))
			Set(0.38f, FLinearColor(0.7f, 0.55f, 0.4f), 0.4f);
		else if (ObjectType == TEXT("cmb_background"))
			Set(0.15f, FLinearColor(0.3f, 0.1f, 0.15f), 0.12f);
		else
			Set(0.2f, FLinearColor::Gray, 0.3f);
		break;

	case EUniverseSignalMode::Radio:
		if (ObjectType == TEXT("quasar"))
			Set(1.f, FLinearColor(1.f, 0.85f, 0.6f), 1.f, false, 2.8f);
		else if (ObjectType == TEXT("magnetar"))
			Set(1.f, FLinearColor(1.f, 0.7f, 0.5f), 1.f);
		else if (ObjectType == TEXT("cmb_background"))
			Set(0.45f, FLinearColor(0.5f, 0.35f, 0.4f), 0.28f);
		else if (ObjectType == TEXT("galaxy"))
			Set(0.32f, FLinearColor(0.6f, 0.55f, 0.7f), 0.5f);
		else if (ObjectType == TEXT("lyman_alpha_blob"))
			Set(0.28f, FLinearColor(0.4f, 0.8f, 0.6f), 0.25f);
		else if (ObjectType == TEXT("cosmic_web_filament"))
			Set(0.28f, FLinearColor(0.55f, 0.45f, 0.7f), 0.4f);
		else
			Set(0.18f, FLinearColor(0.35f, 0.35f, 0.45f), 0.25f);
		break;

	case EUniverseSignalMode::Microwave:
		if (ObjectType == TEXT("cmb_background"))
			Set(1.f, FLinearColor(0.9f, 0.45f, 0.55f), 0.45f);
		else
			Set(0.18f, FLinearColor(0.25f, 0.25f, 0.3f), 0.12f);
		break;

	case EUniverseSignalMode::XRay:
		if (ObjectType == TEXT("magnetar") || ObjectType == TEXT("black_hole") || ObjectType == TEXT("quasar"))
			Set(1.f, FLinearColor(0.75f, 0.9f, 1.f), 1.f, false, 1.1f);
		else if (ObjectType == TEXT("lyman_alpha_blob"))
			Set(0.35f, FLinearColor(0.4f, 0.85f, 1.f), 0.3f);
		else
			Set(0.14f, FLinearColor(0.2f, 0.3f, 0.4f), 0.15f);
		break;

	case EUniverseSignalMode::GammaRay:
		if (ObjectType == TEXT("magnetar") || ObjectType == TEXT("black_hole") || ObjectType == TEXT("quasar"))
			Set(1.f, FLinearColor(0.9f, 0.75f, 1.f), 1.f);
		else if (ObjectType == TEXT("lyman_alpha_blob"))
			Set(0.22f, FLinearColor(0.5f, 0.4f, 0.7f), 0.2f);
		else
			Set(0.12f, FLinearColor(0.25f, 0.2f, 0.35f), 0.12f);
		break;

	case EUniverseSignalMode::GravitationalWave:
		if (ObjectType == TEXT("black_hole") || ObjectType == TEXT("magnetar") || ObjectType == TEXT("quasar"))
			Set(0.88f, FLinearColor(0.55f, 0.65f, 1.f), 0.85f, true);
		else
			Set(0.1f, FLinearColor(0.15f, 0.15f, 0.2f), 0.08f, true);
		break;

	case EUniverseSignalMode::Neutrino:
		if (ObjectType == TEXT("black_hole") || ObjectType == TEXT("magnetar") || ObjectType == TEXT("quasar"))
			Set(0.82f, FLinearColor(0.5f, 0.85f, 0.9f), 0.8f, true);
		else
			Set(0.11f, FLinearColor(0.2f, 0.35f, 0.35f), 0.1f, true);
		break;

	case EUniverseSignalMode::WeakLensing:
		if (ObjectType == TEXT("cosmic_web_filament"))
			Set(1.f, FLinearColor(0.65f, 0.55f, 0.95f), 0.75f);
		else if (ObjectType == TEXT("cosmic_web_node") || ObjectType == TEXT("void"))
			Set(0.92f, FLinearColor(0.85f, 0.6f, 0.45f), 0.7f);
		else if (ObjectType == TEXT("galaxy"))
			Set(0.92f, FLinearColor(0.7f, 0.75f, 1.f), 0.65f);
		else if (ObjectType == TEXT("quasar") || ObjectType == TEXT("lyman_alpha_blob"))
			Set(0.42f, FLinearColor(0.55f, 0.6f, 0.75f), 0.4f);
		else
			Set(0.35f, FLinearColor(0.5f, 0.5f, 0.6f), 0.35f);
		break;

	case EUniverseSignalMode::DarkMatterInference:
		if (ObjectType == TEXT("cosmic_web_filament") || ObjectType == TEXT("void"))
			Set(1.f, FLinearColor(0.45f, 0.35f, 0.75f), 0.8f);
		else if (ObjectType == TEXT("cosmic_web_node"))
			Set(0.95f, FLinearColor(0.7f, 0.45f, 0.35f), 0.75f);
		else if (ObjectType == TEXT("galaxy"))
			Set(0.55f, FLinearColor(0.4f, 0.45f, 0.55f), 0.45f);
		else if (ObjectType == TEXT("quasar") || ObjectType == TEXT("lyman_alpha_blob"))
			Set(0.12f, FLinearColor(0.2f, 0.15f, 0.25f), 0.15f);
		else
			Set(0.35f, FLinearColor(0.35f, 0.3f, 0.5f), 0.35f);
		break;

	case EUniverseSignalMode::SpeculativeNowSignal:
		if (ObjectType == TEXT("quasar") || ObjectType == TEXT("lyman_alpha_blob") || ObjectType == TEXT("black_hole"))
			Set(0.92f, FLinearColor(0.95f, 0.35f, 0.85f), 0.9f);
		else if (ObjectType == TEXT("void"))
			Set(0.75f, FLinearColor(0.4f, 0.2f, 0.6f), 0.5f);
		else
			Set(0.14f, FLinearColor(0.25f, 0.15f, 0.3f), 0.12f);
		break;

	case EUniverseSignalMode::Ultraviolet:
		if (ObjectType == TEXT("lyman_alpha_blob"))
			Set(1.f, FLinearColor(0.25f, 1.f, 0.85f), 0.5f);
		else if (ObjectType == TEXT("galaxy") || ObjectType == TEXT("quasar"))
			Set(0.85f, FLinearColor(0.5f, 0.85f, 1.f), 0.85f);
		else
			Set(0.22f, FLinearColor(0.4f, 0.6f, 0.8f), 0.25f);
		break;

	case EUniverseSignalMode::Infrared:
		if (ObjectType == TEXT("galaxy") || ObjectType == TEXT("quasar") || ObjectType == TEXT("lyman_alpha_blob"))
			Set(0.75f, FLinearColor(1.f, 0.65f, 0.45f), 0.8f);
		else
			Set(0.28f, FLinearColor(0.7f, 0.5f, 0.4f), 0.35f);
		break;

	default:
		Set(0.5f, FLinearColor::White, 0.5f);
		break;
	}

	return V;
}

bool UUniverseSignalModeSubsystem::IsSpeculativeMode() const
{
	return CurrentMode == EUniverseSignalMode::SpeculativeNowSignal;
}
