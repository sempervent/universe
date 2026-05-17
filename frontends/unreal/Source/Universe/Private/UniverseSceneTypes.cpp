#include "UniverseSceneTypes.h"
#include "Dom/JsonObject.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

FCosmicVector3 FCosmicVector3::FromJson(const TSharedPtr<FJsonObject>& Obj)
{
	FCosmicVector3 V;
	if (!Obj.IsValid())
	{
		return V;
	}
	V.X = Obj->GetNumberField(TEXT("x"));
	V.Y = Obj->GetNumberField(TEXT("y"));
	V.Z = Obj->GetNumberField(TEXT("z"));
	return V;
}

FCosmicVisualHints FCosmicVisualHints::FromJson(const TSharedPtr<FJsonObject>& Obj)
{
	FCosmicVisualHints H;
	if (!Obj.IsValid())
	{
		return H;
	}
	if (Obj->HasField(TEXT("color")))
	{
		H.Color = Obj->GetStringField(TEXT("color"));
	}
	if (Obj->HasField(TEXT("emissive")))
	{
		H.bEmissive = Obj->GetBoolField(TEXT("emissive"));
	}
	if (Obj->HasField(TEXT("opacity")))
	{
		H.Opacity = static_cast<float>(Obj->GetNumberField(TEXT("opacity")));
	}
	if (Obj->HasField(TEXT("scale")))
	{
		H.Scale = static_cast<float>(Obj->GetNumberField(TEXT("scale")));
	}
	if (Obj->HasField(TEXT("glow")))
	{
		H.bGlow = Obj->GetBoolField(TEXT("glow"));
	}
	if (Obj->HasField(TEXT("label")))
	{
		H.Label = Obj->GetStringField(TEXT("label"));
	}
	return H;
}

FCosmicRelationship FCosmicRelationship::FromJson(const TSharedPtr<FJsonObject>& Obj)
{
	FCosmicRelationship R;
	if (!Obj.IsValid())
	{
		return R;
	}
	R.TargetId = Obj->GetStringField(TEXT("target_id"));
	R.Relation = Obj->GetStringField(TEXT("relation"));
	if (Obj->HasField(TEXT("description")))
	{
		R.Description = Obj->GetStringField(TEXT("description"));
	}
	return R;
}

FCosmicObject FCosmicObject::FromJson(const TSharedPtr<FJsonObject>& Obj)
{
	FCosmicObject O;
	if (!Obj.IsValid())
	{
		return O;
	}
	O.Id = Obj->GetStringField(TEXT("id"));
	O.Name = Obj->GetStringField(TEXT("name"));
	O.Type = Obj->GetStringField(TEXT("type"));
	O.PositionMpc = FCosmicVector3::FromJson(Obj->GetObjectField(TEXT("position_mpc")));
	O.Redshift = static_cast<float>(Obj->GetNumberField(TEXT("redshift")));
	if (Obj->HasField(TEXT("description")))
	{
		O.Description = Obj->GetStringField(TEXT("description"));
	}
	if (Obj->HasField(TEXT("visual")))
	{
		O.Visual = FCosmicVisualHints::FromJson(Obj->GetObjectField(TEXT("visual")));
	}
	const TArray<TSharedPtr<FJsonValue>>* Rels = nullptr;
	if (Obj->TryGetArrayField(TEXT("relationships"), Rels) && Rels)
	{
		for (const TSharedPtr<FJsonValue>& Val : *Rels)
		{
			O.Relationships.Add(FCosmicRelationship::FromJson(Val->AsObject()));
		}
	}
	return O;
}

FCosmicWebNode FCosmicWebNode::FromJson(const TSharedPtr<FJsonObject>& Obj)
{
	FCosmicWebNode N;
	if (!Obj.IsValid())
	{
		return N;
	}
	N.Id = Obj->GetStringField(TEXT("id"));
	N.PositionMpc = FCosmicVector3::FromJson(Obj->GetObjectField(TEXT("position_mpc")));
	N.Density = static_cast<float>(Obj->GetNumberField(TEXT("density")));
	if (Obj->HasField(TEXT("node_class")))
	{
		N.NodeClass = Obj->GetStringField(TEXT("node_class"));
	}
	return N;
}

FCosmicWebFilament FCosmicWebFilament::FromJson(const TSharedPtr<FJsonObject>& Obj)
{
	FCosmicWebFilament F;
	if (!Obj.IsValid())
	{
		return F;
	}
	F.Id = Obj->GetStringField(TEXT("id"));
	F.StartNodeId = Obj->GetStringField(TEXT("start_node_id"));
	F.EndNodeId = Obj->GetStringField(TEXT("end_node_id"));
	F.Density = static_cast<float>(Obj->GetNumberField(TEXT("density")));
	F.RadiusMpc = static_cast<float>(Obj->GetNumberField(TEXT("radius_mpc")));
	const TArray<TSharedPtr<FJsonValue>>* Cps = nullptr;
	if (Obj->TryGetArrayField(TEXT("control_points_mpc"), Cps) && Cps)
	{
		for (const TSharedPtr<FJsonValue>& Val : *Cps)
		{
			F.ControlPointsMpc.Add(FCosmicVector3::FromJson(Val->AsObject()));
		}
	}
	return F;
}

FUniverseSceneMetadata FUniverseSceneMetadata::FromJson(const TSharedPtr<FJsonObject>& Obj)
{
	FUniverseSceneMetadata M;
	if (!Obj.IsValid())
	{
		return M;
	}
	if (Obj->HasField(TEXT("scene_class")))
	{
		M.SceneClass = Obj->GetStringField(TEXT("scene_class"));
	}
	if (Obj->HasField(TEXT("recommended_camera_target_object_id")))
	{
		M.RecommendedCameraTargetObjectId = Obj->GetStringField(TEXT("recommended_camera_target_object_id"));
	}
	if (Obj->HasField(TEXT("recommended_initial_signal_mode")))
	{
		M.RecommendedInitialSignalMode = Obj->GetStringField(TEXT("recommended_initial_signal_mode"));
	}
	const TArray<TSharedPtr<FJsonValue>>* Featured = nullptr;
	if (Obj->TryGetArrayField(TEXT("featured_object_ids"), Featured) && Featured)
	{
		for (const TSharedPtr<FJsonValue>& Val : *Featured)
		{
			M.FeaturedObjectIds.Add(Val->AsString());
		}
	}
	if (Obj->HasField(TEXT("teaching_summary")))
	{
		M.TeachingSummary = Obj->GetStringField(TEXT("teaching_summary"));
	}
	if (Obj->HasField(TEXT("scale_description")))
	{
		M.ScaleDescription = Obj->GetStringField(TEXT("scale_description"));
	}
	if (Obj->HasField(TEXT("description")))
	{
		M.Description = Obj->GetStringField(TEXT("description"));
	}
	return M;
}

bool FUniverseSceneRegion::IsDeepField() const
{
	if (Metadata.SceneClass.Equals(TEXT("deep_field"), ESearchCase::IgnoreCase))
	{
		return true;
	}
	if (Id.Equals(TEXT("scene-001"), ESearchCase::IgnoreCase))
	{
		return true;
	}
	return Redshift > 0.08f && (Filaments.Num() > 0 || Nodes.Num() > 0);
}

bool FUniverseSceneRegion::IsSolarSystem() const
{
	if (Metadata.SceneClass.Equals(TEXT("solar_system"), ESearchCase::IgnoreCase))
	{
		return true;
	}
	return Id.Equals(TEXT("solar-system"), ESearchCase::IgnoreCase);
}

bool FUniverseSceneRegion::ParseFromJsonString(
	const FString& JsonText,
	FUniverseSceneRegion& OutScene,
	FString& OutError)
{
	TSharedPtr<FJsonObject> Root;
	const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
	if (!FJsonSerializer::Deserialize(Reader, Root) || !Root.IsValid())
	{
		OutError = TEXT("Failed to parse scene JSON");
		return false;
	}

	OutScene.Id = Root->GetStringField(TEXT("id"));
	OutScene.Name = Root->GetStringField(TEXT("name"));
	OutScene.Seed = Root->GetStringField(TEXT("seed"));
	OutScene.Redshift = static_cast<float>(Root->GetNumberField(TEXT("redshift")));
	OutScene.SizeMpc = static_cast<float>(Root->GetNumberField(TEXT("size_mpc")));

	if (Root->HasField(TEXT("metadata")))
	{
		OutScene.Metadata = FUniverseSceneMetadata::FromJson(Root->GetObjectField(TEXT("metadata")));
	}

	const TArray<TSharedPtr<FJsonValue>>* Objects = nullptr;
	if (Root->TryGetArrayField(TEXT("objects"), Objects) && Objects)
	{
		for (const TSharedPtr<FJsonValue>& Val : *Objects)
		{
			OutScene.Objects.Add(FCosmicObject::FromJson(Val->AsObject()));
		}
	}

	const TArray<TSharedPtr<FJsonValue>>* NodesArr = nullptr;
	if (Root->TryGetArrayField(TEXT("nodes"), NodesArr) && NodesArr)
	{
		for (const TSharedPtr<FJsonValue>& Val : *NodesArr)
		{
			OutScene.Nodes.Add(FCosmicWebNode::FromJson(Val->AsObject()));
		}
	}

	const TArray<TSharedPtr<FJsonValue>>* Fils = nullptr;
	if (Root->TryGetArrayField(TEXT("filaments"), Fils) && Fils)
	{
		for (const TSharedPtr<FJsonValue>& Val : *Fils)
		{
			OutScene.Filaments.Add(FCosmicWebFilament::FromJson(Val->AsObject()));
		}
	}

	return true;
}
