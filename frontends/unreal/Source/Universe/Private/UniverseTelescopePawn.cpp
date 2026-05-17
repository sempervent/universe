#include "UniverseTelescopePawn.h"
#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Kismet/GameplayStatics.h"
#include "UniverseObjectActor.h"
#include "UniverseSceneActor.h"
#include "UniverseSignalModeSubsystem.h"

AUniverseTelescopePawn::AUniverseTelescopePawn()
{
	PrimaryActorTick.bCanEverTick = true;

	SpringArm = CreateDefaultSubobject<USpringArmComponent>(TEXT("SpringArm"));
	SpringArm->TargetArmLength = 900.f;
	SpringArm->bDoCollisionTest = false;
	SpringArm->bEnableCameraLag = true;
	SpringArm->CameraLagSpeed = 6.f;
	RootComponent = SpringArm;

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(SpringArm, USpringArmComponent::SocketName);
}

void AUniverseTelescopePawn::BeginPlay()
{
	Super::BeginPlay();

	if (UGameInstance* GI = GetGameInstance())
	{
		if (UUniverseSignalModeSubsystem* Sig = GI->GetSubsystem<UUniverseSignalModeSubsystem>())
		{
			Sig->OnSignalModeChanged.AddDynamic(this, &AUniverseTelescopePawn::OnSignalModeChanged);
		}
	}

	FTimerHandle Handle;
	GetWorldTimerManager().SetTimer(
		Handle,
		this,
		&AUniverseTelescopePawn::FocusSelectedOrRecommended,
		0.35f,
		false);
}

void AUniverseTelescopePawn::OnSignalModeChanged()
{
	if (AUniverseSceneActor* Scene = GetSceneActor())
	{
		Scene->ApplySignalModeToScene();
	}
}

AUniverseSceneActor* AUniverseTelescopePawn::GetSceneActor() const
{
	TArray<AActor*> Found;
	UGameplayStatics::GetAllActorsOfClass(GetWorld(), AUniverseSceneActor::StaticClass(), Found);
	if (Found.Num() > 0)
	{
		return Cast<AUniverseSceneActor>(Found[0]);
	}
	return nullptr;
}

void AUniverseTelescopePawn::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);
	PlayerInputComponent->BindAxis(TEXT("OrbitYaw"), this, &AUniverseTelescopePawn::OrbitYaw);
	PlayerInputComponent->BindAxis(TEXT("OrbitPitch"), this, &AUniverseTelescopePawn::OrbitPitch);
	PlayerInputComponent->BindAxis(TEXT("Zoom"), this, &AUniverseTelescopePawn::ZoomArm);
	PlayerInputComponent->BindAction(TEXT("CycleSignalMode"), IE_Pressed, this, &AUniverseTelescopePawn::CycleSignalMode);
	PlayerInputComponent->BindAction(TEXT("FocusRecommended"), IE_Pressed, this, &AUniverseTelescopePawn::FocusSelectedOrRecommended);
	PlayerInputComponent->BindAction(TEXT("ResetCamera"), IE_Pressed, this, &AUniverseTelescopePawn::ResetTelescopeView);
	PlayerInputComponent->BindAction(TEXT("ToggleLabels"), IE_Pressed, this, &AUniverseTelescopePawn::ToggleLabels);
	PlayerInputComponent->BindAction(TEXT("SelectObject"), IE_Released, this, &AUniverseTelescopePawn::SelectObjectUnderCursor);
	PlayerInputComponent->BindAction(TEXT("CycleFeatured"), IE_Pressed, this, &AUniverseTelescopePawn::CycleFeaturedTarget);
}

void AUniverseTelescopePawn::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	SetActorLocation(FocusTarget);
}

void AUniverseTelescopePawn::OrbitYaw(float Value)
{
	if (!FMath::IsNearlyZero(Value))
	{
		SpringArm->AddRelativeRotation(FRotator(0.f, Value * OrbitSpeed * 50.f, 0.f));
	}
}

void AUniverseTelescopePawn::OrbitPitch(float Value)
{
	if (!FMath::IsNearlyZero(Value))
	{
		FRotator R = SpringArm->GetRelativeRotation();
		R.Pitch = FMath::Clamp(R.Pitch + Value * OrbitSpeed * 50.f, -80.f, -5.f);
		SpringArm->SetRelativeRotation(R);
	}
}

void AUniverseTelescopePawn::ZoomArm(float Value)
{
	if (!FMath::IsNearlyZero(Value))
	{
		SpringArm->TargetArmLength = FMath::Clamp(
			SpringArm->TargetArmLength - Value * ZoomSpeed,
			MinArmLength,
			MaxArmLength);
	}
}

void AUniverseTelescopePawn::FocusOnLocation(const FVector& WorldLocation, float FitRadius)
{
	FocusTarget = WorldLocation;
	SpringArm->TargetArmLength = FMath::Clamp(FitRadius * 3.35f, MinArmLength, MaxArmLength * 0.45f);
}

void AUniverseTelescopePawn::FocusSelectedOrRecommended()
{
	if (AUniverseSceneActor* Scene = GetSceneActor())
	{
		const FVector Loc = Scene->GetFocusLocation();
		float Radius = 220.f;
		if (Scene->SelectedObject)
		{
			if (Scene->SelectedObject->ObjectType == TEXT("lyman_alpha_blob"))
			{
				Radius = 280.f;
			}
		}
		FocusOnLocation(Loc, Radius);
	}
}

void AUniverseTelescopePawn::ResetTelescopeView()
{
	SpringArm->SetRelativeRotation(FRotator(-25.f, 35.f, 0.f));
	if (AUniverseSceneActor* Scene = GetSceneActor())
	{
		Scene->ClearSelection();
		FocusOnLocation(Scene->GetRecommendedCameraFocus(), 220.f);
	}
}

void AUniverseTelescopePawn::SelectObjectUnderCursor()
{
	APlayerController* PC = Cast<APlayerController>(GetController());
	if (!PC)
	{
		return;
	}

	FHitResult Hit;
	if (!PC->GetHitResultUnderCursor(ECC_Visibility, false, Hit))
	{
		return;
	}

	if (AUniverseSceneActor* Scene = GetSceneActor())
	{
		if (!Scene->SelectObjectFromHit(Hit))
		{
			Scene->ClearSelection();
		}
	}
}

void AUniverseTelescopePawn::CycleSignalMode()
{
	if (UGameInstance* GI = GetGameInstance())
	{
		if (UUniverseSignalModeSubsystem* Sig = GI->GetSubsystem<UUniverseSignalModeSubsystem>())
		{
			Sig->CycleMode();
		}
	}
}

void AUniverseTelescopePawn::ToggleLabels()
{
	bLabelsEnabled = !bLabelsEnabled;
	if (AUniverseSceneActor* Scene = GetSceneActor())
	{
		Scene->bLabelsEnabled = bLabelsEnabled;
		Scene->RefreshLabelVisibility();
	}
}

void AUniverseTelescopePawn::CycleFeaturedTarget()
{
	if (AUniverseSceneActor* Scene = GetSceneActor())
	{
		Scene->CycleFeaturedTarget();
		FocusSelectedOrRecommended();
	}
}
