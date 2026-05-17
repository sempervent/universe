#include "UniverseGameMode.h"
#include "UniverseTelescopeHUD.h"
#include "UniverseTelescopePawn.h"

AUniverseGameMode::AUniverseGameMode()
{
	DefaultPawnClass = AUniverseTelescopePawn::StaticClass();
	HUDClass = AUniverseTelescopeHUD::StaticClass();
}
