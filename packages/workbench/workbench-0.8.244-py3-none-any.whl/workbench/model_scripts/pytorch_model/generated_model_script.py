# PyTorch Tabular Model Template for Workbench
#
# This template handles both classification and regression models with:
# - K-fold cross-validation ensemble training (or single train/val split)
# - Out-of-fold predictions for validation metrics
# - Categorical feature embedding via TabularMLP
# - Compressed feature decompression
#
# NOTE: Imports are structured to minimize serverless endpoint startup time.
# Heavy imports (sklearn, awswrangler) are deferred to training time.

import json
import os

import joblib
import numpy as np
import pandas as pd
import torch

from model_script_utils import (
    convert_categorical_types,
    decompress_features,
    expand_proba_column,
    input_fn,
    match_features_case_insensitive,
    output_fn,
)
from pytorch_utils import (
    FeatureScaler,
    load_model,
    predict,
    prepare_data,
)
from uq_harness import (
    compute_confidence,
    load_uq_models,
    predict_intervals,
)

# =============================================================================
# Default Hyperparameters
# =============================================================================
DEFAULT_HYPERPARAMETERS = {
    # Training parameters
    "n_folds": 5,
    "max_epochs": 200,
    "early_stopping_patience": 30,
    "batch_size": 128,
    # Model architecture (larger capacity - ensemble provides regularization)
    "layers": "512-256-128",
    "learning_rate": 1e-3,
    "dropout": 0.05,
    "use_batch_norm": True,
    # Loss function for regression (L1Loss=MAE, MSELoss=MSE, HuberLoss, SmoothL1Loss)
    "loss": "L1Loss",
    # Split strategy: "random", "scaffold", or "butina"
    # - random: Standard random split (default)
    # - scaffold: Bemis-Murcko scaffold-based grouping (requires 'smiles' column in data)
    # - butina: Morgan fingerprint clustering (requires 'smiles' column, recommended for ADMET)
    "split_strategy": "random",
    "butina_cutoff": 0.4,  # Tanimoto distance cutoff for Butina clustering
    # Random seed
    "seed": 42,
}

# Template parameters (filled in by Workbench)
TEMPLATE_PARAMS = {
    "model_type": "classifier",
    "target": "class",
    "features": ['chi2v', 'fr_sulfone', 'chi1v', 'bcut2d_logplow', 'fr_piperzine', 'kappa3', 'smr_vsa1', 'slogp_vsa5', 'fr_ketone_topliss', 'fr_sulfonamd', 'fr_imine', 'fr_benzene', 'fr_ester', 'chi2n', 'labuteasa', 'peoe_vsa2', 'smr_vsa6', 'bcut2d_chglo', 'fr_sh', 'peoe_vsa1', 'fr_allylic_oxid', 'chi4n', 'fr_ar_oh', 'fr_nh0', 'fr_term_acetylene', 'slogp_vsa7', 'slogp_vsa4', 'estate_vsa1', 'vsa_estate4', 'numbridgeheadatoms', 'numheterocycles', 'fr_ketone', 'fr_morpholine', 'fr_guanido', 'estate_vsa2', 'numheteroatoms', 'fr_nitro_arom_nonortho', 'fr_piperdine', 'nocount', 'numspiroatoms', 'fr_aniline', 'fr_thiophene', 'slogp_vsa10', 'fr_amide', 'slogp_vsa2', 'fr_epoxide', 'vsa_estate7', 'fr_ar_coo', 'fr_imidazole', 'fr_nitrile', 'fr_oxazole', 'numsaturatedrings', 'fr_pyridine', 'fr_hoccn', 'fr_ndealkylation1', 'numaliphaticheterocycles', 'fr_phenol', 'maxpartialcharge', 'vsa_estate5', 'peoe_vsa13', 'minpartialcharge', 'qed', 'fr_al_oh', 'slogp_vsa11', 'chi0n', 'fr_bicyclic', 'peoe_vsa12', 'fpdensitymorgan1', 'fr_oxime', 'molwt', 'fr_dihydropyridine', 'smr_vsa5', 'peoe_vsa5', 'fr_nitro', 'hallkieralpha', 'heavyatommolwt', 'fr_alkyl_halide', 'peoe_vsa8', 'fr_nhpyrrole', 'fr_isocyan', 'bcut2d_chghi', 'fr_lactam', 'peoe_vsa11', 'smr_vsa9', 'tpsa', 'chi4v', 'slogp_vsa1', 'phi', 'bcut2d_logphi', 'avgipc', 'estate_vsa11', 'fr_coo', 'bcut2d_mwhi', 'numunspecifiedatomstereocenters', 'vsa_estate10', 'estate_vsa8', 'numvalenceelectrons', 'fr_nh2', 'fr_lactone', 'vsa_estate1', 'estate_vsa4', 'numatomstereocenters', 'vsa_estate8', 'fr_para_hydroxylation', 'peoe_vsa3', 'fr_thiazole', 'peoe_vsa10', 'fr_ndealkylation2', 'slogp_vsa12', 'peoe_vsa9', 'maxestateindex', 'fr_quatn', 'smr_vsa7', 'minestateindex', 'numaromaticheterocycles', 'numrotatablebonds', 'fr_ar_nh', 'fr_ether', 'exactmolwt', 'fr_phenol_noorthohbond', 'slogp_vsa3', 'fr_ar_n', 'sps', 'fr_c_o_nocoo', 'bertzct', 'peoe_vsa7', 'slogp_vsa8', 'numradicalelectrons', 'molmr', 'fr_tetrazole', 'numsaturatedcarbocycles', 'bcut2d_mrhi', 'kappa1', 'numamidebonds', 'fpdensitymorgan2', 'smr_vsa8', 'chi1n', 'estate_vsa6', 'fr_barbitur', 'fr_diazo', 'kappa2', 'chi0', 'bcut2d_mrlow', 'balabanj', 'peoe_vsa4', 'numhacceptors', 'fr_sulfide', 'chi3n', 'smr_vsa2', 'fr_al_oh_notert', 'fr_benzodiazepine', 'fr_phos_ester', 'fr_aldehyde', 'fr_coo2', 'estate_vsa5', 'fr_prisulfonamd', 'numaromaticcarbocycles', 'fr_unbrch_alkane', 'fr_urea', 'fr_nitroso', 'smr_vsa10', 'fr_c_s', 'smr_vsa3', 'fr_methoxy', 'maxabspartialcharge', 'slogp_vsa9', 'heavyatomcount', 'fr_azide', 'chi3v', 'smr_vsa4', 'mollogp', 'chi0v', 'fr_aryl_methyl', 'fr_nh1', 'fpdensitymorgan3', 'fr_furan', 'fr_hdrzine', 'fr_arn', 'numaromaticrings', 'vsa_estate3', 'fr_azo', 'fr_halogen', 'estate_vsa9', 'fr_hdrzone', 'numhdonors', 'fr_alkyl_carbamate', 'fr_isothiocyan', 'minabspartialcharge', 'fr_al_coo', 'ringcount', 'chi1', 'estate_vsa7', 'fr_nitro_arom', 'vsa_estate9', 'minabsestateindex', 'maxabsestateindex', 'vsa_estate6', 'estate_vsa10', 'estate_vsa3', 'fr_n_o', 'fr_amidine', 'fr_thiocyan', 'fr_phos_acid', 'fr_c_o', 'fr_imide', 'numaliphaticrings', 'peoe_vsa6', 'vsa_estate2', 'nhohcount', 'numsaturatedheterocycles', 'slogp_vsa6', 'peoe_vsa14', 'fractioncsp3', 'bcut2d_mwlow', 'numaliphaticcarbocycles', 'fr_priamide', 'nacid', 'nbase', 'naromatom', 'narombond', 'sz', 'sm', 'sv', 'sse', 'spe', 'sare', 'sp', 'si', 'mz', 'mm', 'mv', 'mse', 'mpe', 'mare', 'mp', 'mi', 'xch_3d', 'xch_4d', 'xch_5d', 'xch_6d', 'xch_7d', 'xch_3dv', 'xch_4dv', 'xch_5dv', 'xch_6dv', 'xch_7dv', 'xc_3d', 'xc_4d', 'xc_5d', 'xc_6d', 'xc_3dv', 'xc_4dv', 'xc_5dv', 'xc_6dv', 'xpc_4d', 'xpc_5d', 'xpc_6d', 'xpc_4dv', 'xpc_5dv', 'xpc_6dv', 'xp_0d', 'xp_1d', 'xp_2d', 'xp_3d', 'xp_4d', 'xp_5d', 'xp_6d', 'xp_7d', 'axp_0d', 'axp_1d', 'axp_2d', 'axp_3d', 'axp_4d', 'axp_5d', 'axp_6d', 'axp_7d', 'xp_0dv', 'xp_1dv', 'xp_2dv', 'xp_3dv', 'xp_4dv', 'xp_5dv', 'xp_6dv', 'xp_7dv', 'axp_0dv', 'axp_1dv', 'axp_2dv', 'axp_3dv', 'axp_4dv', 'axp_5dv', 'axp_6dv', 'axp_7dv', 'c1sp1', 'c2sp1', 'c1sp2', 'c2sp2', 'c3sp2', 'c1sp3', 'c2sp3', 'c3sp3', 'c4sp3', 'hybratio', 'fcsp3', 'num_stereocenters', 'num_unspecified_stereocenters', 'num_defined_stereocenters', 'num_r_centers', 'num_s_centers', 'num_stereobonds', 'num_e_bonds', 'num_z_bonds', 'stereo_complexity', 'frac_defined_stereo'],
    "id_column": "udm_mol_bat_id",
    "compressed_features": [],
    "model_metrics_s3_path": "s3://ideaya-sageworks-bucket/models/pka-b1-value-class-pytorch-1-dt/training",
    "hyperparameters": {},
}


# =============================================================================
# Model Loading (for SageMaker inference)
# =============================================================================
def model_fn(model_dir: str) -> dict:
    """Load PyTorch TabularMLP ensemble from the specified directory."""
    # Load ensemble metadata
    metadata_path = os.path.join(model_dir, "ensemble_metadata.joblib")
    if os.path.exists(metadata_path):
        metadata = joblib.load(metadata_path)
        n_ensemble = metadata["n_ensemble"]
    else:
        n_ensemble = 1

    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"

    # Load ensemble models
    ensemble_models = []
    for i in range(n_ensemble):
        model_path = os.path.join(model_dir, f"model_{i}")
        model = load_model(model_path, device=device)
        ensemble_models.append(model)

    print(f"Loaded {len(ensemble_models)} model(s)")

    # Load feature scaler
    scaler = FeatureScaler.load(os.path.join(model_dir, "scaler.joblib"))

    # Load UQ models (regression only)
    uq_models, uq_metadata = None, None
    uq_path = os.path.join(model_dir, "uq_metadata.json")
    if os.path.exists(uq_path):
        uq_models, uq_metadata = load_uq_models(model_dir)

    return {
        "ensemble_models": ensemble_models,
        "n_ensemble": n_ensemble,
        "scaler": scaler,
        "uq_models": uq_models,
        "uq_metadata": uq_metadata,
    }


# =============================================================================
# Inference (for SageMaker inference)
# =============================================================================
def predict_fn(df: pd.DataFrame, model_dict: dict) -> pd.DataFrame:
    """Make predictions with PyTorch TabularMLP ensemble."""
    model_type = TEMPLATE_PARAMS["model_type"]
    compressed_features = TEMPLATE_PARAMS["compressed_features"]
    model_dir = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")

    # Load artifacts
    ensemble_models = model_dict["ensemble_models"]
    scaler = model_dict["scaler"]
    uq_models = model_dict.get("uq_models")
    uq_metadata = model_dict.get("uq_metadata")

    with open(os.path.join(model_dir, "feature_columns.json")) as f:
        features = json.load(f)
    with open(os.path.join(model_dir, "category_mappings.json")) as f:
        category_mappings = json.load(f)
    with open(os.path.join(model_dir, "feature_metadata.json")) as f:
        feature_metadata = json.load(f)

    continuous_cols = feature_metadata["continuous_cols"]
    categorical_cols = feature_metadata["categorical_cols"]

    label_encoder = None
    encoder_path = os.path.join(model_dir, "label_encoder.joblib")
    if os.path.exists(encoder_path):
        label_encoder = joblib.load(encoder_path)

    print(f"Model Features: {features}")

    # Prepare features
    matched_df = match_features_case_insensitive(df, features)
    matched_df, _ = convert_categorical_types(matched_df, features, category_mappings)

    if compressed_features:
        print("Decompressing features for prediction...")
        matched_df, features = decompress_features(matched_df, features, compressed_features)

    # Impute missing values (categorical with mode, continuous handled by scaler)
    missing_counts = matched_df[features].isna().sum()
    if missing_counts.any():
        missing_features = missing_counts[missing_counts > 0]
        print(f"Imputing missing values: {missing_features.to_dict()}")

        # Load categorical imputation values if available
        impute_path = os.path.join(model_dir, "categorical_impute.json")
        if os.path.exists(impute_path):
            with open(impute_path) as f:
                cat_impute_values = json.load(f)
            for col in categorical_cols:
                if col in cat_impute_values and matched_df[col].isna().any():
                    matched_df[col] = matched_df[col].fillna(cat_impute_values[col])
        # Continuous features are imputed by FeatureScaler.transform() using column means

    # Initialize output columns
    df["prediction"] = np.nan
    if model_type in ["regressor", "uq_regressor"]:
        df["prediction_std"] = np.nan

    # Prepare data for inference (with standardization and continuous imputation)
    x_cont, x_cat, _, _, _ = prepare_data(
        matched_df, continuous_cols, categorical_cols, category_mappings=category_mappings, scaler=scaler
    )

    # Collect ensemble predictions
    all_preds = []
    for model in ensemble_models:
        preds = predict(model, x_cont, x_cat)
        all_preds.append(preds)

    # Aggregate predictions
    ensemble_preds = np.stack(all_preds, axis=0)
    preds = np.mean(ensemble_preds, axis=0)
    preds_std = np.std(ensemble_preds, axis=0)

    print(f"Inference complete: {len(preds)} predictions, {len(ensemble_models)} ensemble members")

    if label_encoder is not None:
        # Classification: average probabilities, then argmax
        avg_probs = preds  # Already softmax output
        class_preds = np.argmax(avg_probs, axis=1)
        predictions = label_encoder.inverse_transform(class_preds)

        df["pred_proba"] = [p.tolist() for p in avg_probs]
        df = expand_proba_column(df, label_encoder.classes_)
    else:
        # Regression
        predictions = preds.flatten()
        df["prediction_std"] = preds_std.flatten()

        # Add UQ intervals if available
        if uq_models and uq_metadata:
            df["prediction"] = predictions  # Set prediction before compute_confidence
            df = predict_intervals(df, matched_df[features], uq_models, uq_metadata)
            df = compute_confidence(df, uq_metadata["median_interval_width"], "q_10", "q_90")

    df["prediction"] = predictions
    return df


# =============================================================================
# Training
# =============================================================================
if __name__ == "__main__":
    # -------------------------------------------------------------------------
    # Training-only imports (deferred to reduce serverless startup time)
    # -------------------------------------------------------------------------
    import argparse

    import awswrangler as wr
    from sklearn.model_selection import KFold, StratifiedKFold, train_test_split
    from sklearn.preprocessing import LabelEncoder

    # Enable Tensor Core optimization for GPUs that support it
    torch.set_float32_matmul_precision("medium")

    from model_script_utils import (
        check_dataframe,
        compute_classification_metrics,
        compute_regression_metrics,
        get_split_indices,
        print_classification_metrics,
        print_confusion_matrix,
        print_regression_metrics,
    )
    from pytorch_utils import (
        create_model,
        save_model,
        train_model,
    )
    from uq_harness import (
        save_uq_models,
        train_uq_models,
    )

    # -------------------------------------------------------------------------
    # Setup: Parse arguments and load data
    # -------------------------------------------------------------------------
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", type=str, default=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
    parser.add_argument("--train", type=str, default=os.environ.get("SM_CHANNEL_TRAIN", "/opt/ml/input/data/train"))
    parser.add_argument("--output-data-dir", type=str, default=os.environ.get("SM_OUTPUT_DATA_DIR", "/opt/ml/output/data"))
    args = parser.parse_args()

    # Extract template parameters
    target = TEMPLATE_PARAMS["target"]
    features = TEMPLATE_PARAMS["features"]
    orig_features = features.copy()
    id_column = TEMPLATE_PARAMS["id_column"]
    compressed_features = TEMPLATE_PARAMS["compressed_features"]
    model_type = TEMPLATE_PARAMS["model_type"]
    model_metrics_s3_path = TEMPLATE_PARAMS["model_metrics_s3_path"]
    hyperparameters = {**DEFAULT_HYPERPARAMETERS, **(TEMPLATE_PARAMS["hyperparameters"] or {})}

    # Load training data
    training_files = [os.path.join(args.train, f) for f in os.listdir(args.train) if f.endswith(".csv")]
    print(f"Training Files: {training_files}")
    all_df = pd.concat([pd.read_csv(f, engine="python") for f in training_files])
    check_dataframe(all_df, "training_df")

    # Drop rows with missing target (required for training)
    initial_count = len(all_df)
    all_df = all_df.dropna(subset=[target])
    if len(all_df) < initial_count:
        print(f"Dropped {initial_count - len(all_df)} rows with missing target")

    print(f"Target: {target}")
    print(f"Features: {features}")
    print(f"Hyperparameters: {hyperparameters}")

    # -------------------------------------------------------------------------
    # Preprocessing
    # -------------------------------------------------------------------------
    all_df, category_mappings = convert_categorical_types(all_df, features)

    if compressed_features:
        print(f"Decompressing features: {compressed_features}")
        all_df, features = decompress_features(all_df, features, compressed_features)

    # Determine categorical vs continuous columns
    categorical_cols = [c for c in features if all_df[c].dtype.name == "category"]
    continuous_cols = [c for c in features if c not in categorical_cols]
    all_df[continuous_cols] = all_df[continuous_cols].astype("float64")
    print(f"Categorical: {categorical_cols}")
    print(f"Continuous: {len(continuous_cols)} columns")

    # Report and handle missing values in features
    # Compute categorical imputation values (mode) for use at inference time
    cat_impute_values = {}
    for col in categorical_cols:
        mode_val = all_df[col].mode().iloc[0] if not all_df[col].mode().empty else all_df[col].cat.categories[0]
        cat_impute_values[col] = str(mode_val)  # Convert to string for JSON serialization

    missing_counts = all_df[features].isna().sum()
    if missing_counts.any():
        missing_features = missing_counts[missing_counts > 0]
        print(f"Missing values in features (will be imputed): {missing_features.to_dict()}")
        # Impute categorical features with mode (most frequent value)
        for col in categorical_cols:
            if all_df[col].isna().any():
                all_df[col] = all_df[col].fillna(cat_impute_values[col])
        # Continuous features are imputed by FeatureScaler.transform() using column means

    # -------------------------------------------------------------------------
    # Classification setup
    # -------------------------------------------------------------------------
    label_encoder = None
    n_outputs = 1
    if model_type == "classifier":
        label_encoder = LabelEncoder()
        all_df[target] = label_encoder.fit_transform(all_df[target])
        n_outputs = len(label_encoder.classes_)
        print(f"Class labels: {label_encoder.classes_.tolist()}")

    # -------------------------------------------------------------------------
    # Cross-validation setup
    # -------------------------------------------------------------------------
    n_folds = hyperparameters["n_folds"]
    task = "classification" if model_type == "classifier" else "regression"
    hidden_layers = [int(x) for x in hyperparameters["layers"].split("-")]

    # Get categorical cardinalities
    categorical_cardinalities = [len(category_mappings.get(col, {})) for col in categorical_cols]

    # Get split strategy parameters
    split_strategy = hyperparameters.get("split_strategy", "random")
    butina_cutoff = hyperparameters.get("butina_cutoff", 0.4)

    # Check for pre-defined training column (overrides split strategy)
    if n_folds == 1 and "training" in all_df.columns:
        print("Using 'training' column for train/val split")
        train_idx = np.where(all_df["training"])[0]
        val_idx = np.where(~all_df["training"])[0]
        folds = [(train_idx, val_idx)]
    else:
        # Use unified split interface (auto-detects 'smiles' column for scaffold/butina)
        target_col = target if model_type == "classifier" else None
        folds = get_split_indices(
            all_df,
            n_splits=n_folds,
            strategy=split_strategy,
            target_column=target_col,
            test_size=0.2,
            random_state=42,
            butina_cutoff=butina_cutoff,
        )
        print(f"Split strategy: {split_strategy}")

    print(f"Training {'single model' if n_folds == 1 else f'{n_folds}-fold ensemble'}...")

    # Fit scaler on all training data (used across all folds)
    scaler = FeatureScaler()
    scaler.fit(all_df, continuous_cols)
    print(f"Fitted scaler on {len(continuous_cols)} continuous features")

    # Determine device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # -------------------------------------------------------------------------
    # Training loop
    # -------------------------------------------------------------------------
    oof_predictions = np.full((len(all_df), n_outputs), np.nan, dtype=np.float64)

    ensemble_models = []
    for fold_idx, (train_idx, val_idx) in enumerate(folds):
        print(f"\n{'='*50}")
        print(f"Fold {fold_idx + 1}/{len(folds)} - Train: {len(train_idx)}, Val: {len(val_idx)}")
        print(f"{'='*50}")

        df_train = all_df.iloc[train_idx].reset_index(drop=True)
        df_val = all_df.iloc[val_idx].reset_index(drop=True)

        # Prepare data (using pre-fitted scaler)
        train_x_cont, train_x_cat, train_y, _, _ = prepare_data(
            df_train, continuous_cols, categorical_cols, target, category_mappings, scaler=scaler
        )
        val_x_cont, val_x_cat, val_y, _, _ = prepare_data(
            df_val, continuous_cols, categorical_cols, target, category_mappings, scaler=scaler
        )

        # Create model
        torch.manual_seed(hyperparameters["seed"] + fold_idx)
        model = create_model(
            n_continuous=len(continuous_cols),
            categorical_cardinalities=categorical_cardinalities,
            hidden_layers=hidden_layers,
            n_outputs=n_outputs,
            task=task,
            dropout=hyperparameters["dropout"],
            use_batch_norm=hyperparameters["use_batch_norm"],
        )

        # Train
        model, history = train_model(
            model,
            train_x_cont, train_x_cat, train_y,
            val_x_cont, val_x_cat, val_y,
            task=task,
            max_epochs=hyperparameters["max_epochs"],
            patience=hyperparameters["early_stopping_patience"],
            batch_size=hyperparameters["batch_size"],
            learning_rate=hyperparameters["learning_rate"],
            loss=hyperparameters.get("loss", "L1Loss"),
            device=device,
        )
        ensemble_models.append(model)

        # Out-of-fold predictions
        fold_preds = predict(model, val_x_cont, val_x_cat)
        oof_predictions[val_idx] = fold_preds

    print(f"\nTraining complete! Trained {len(ensemble_models)} model(s).")

    # -------------------------------------------------------------------------
    # Prepare validation results
    # -------------------------------------------------------------------------
    if n_folds == 1:
        val_mask = ~np.isnan(oof_predictions[:, 0])
        df_val = all_df[val_mask].copy()
        predictions = oof_predictions[val_mask]
    else:
        df_val = all_df.copy()
        predictions = oof_predictions

    # Decode labels for classification
    if model_type == "classifier":
        class_preds = np.argmax(predictions, axis=1)
        df_val[target] = label_encoder.inverse_transform(df_val[target].astype(int))
        df_val["prediction"] = label_encoder.inverse_transform(class_preds)
        df_val["pred_proba"] = [p.tolist() for p in predictions]
        df_val = expand_proba_column(df_val, label_encoder.classes_)
    else:
        df_val["prediction"] = predictions.flatten()

    # -------------------------------------------------------------------------
    # Compute and print metrics
    # -------------------------------------------------------------------------
    y_true = df_val[target].values
    y_pred = df_val["prediction"].values

    if model_type == "classifier":
        score_df = compute_classification_metrics(y_true, y_pred, label_encoder.classes_, target)
        print_classification_metrics(score_df, target, label_encoder.classes_)
        print_confusion_matrix(y_true, y_pred, label_encoder.classes_)
    else:
        metrics = compute_regression_metrics(y_true, y_pred)
        print_regression_metrics(metrics)

        # Compute ensemble prediction_std
        if n_folds > 1:
            # Re-run inference with all models to get std
            x_cont, x_cat, _, _, _ = prepare_data(
                df_val, continuous_cols, categorical_cols, category_mappings=category_mappings, scaler=scaler
            )
            all_preds = [predict(m, x_cont, x_cat).flatten() for m in ensemble_models]
            df_val["prediction_std"] = np.std(np.stack(all_preds), axis=0)
            print(f"Ensemble std - mean: {df_val['prediction_std'].mean():.4f}, max: {df_val['prediction_std'].max():.4f}")
        else:
            df_val["prediction_std"] = 0.0

        # Train UQ models for uncertainty quantification
        print("\n" + "=" * 50)
        print("Training UQ Models")
        print("=" * 50)
        uq_models, uq_metadata = train_uq_models(
            all_df[features], all_df[target], df_val[features], y_true
        )
        df_val = predict_intervals(df_val, df_val[features], uq_models, uq_metadata)
        df_val = compute_confidence(df_val, uq_metadata["median_interval_width"])

    # -------------------------------------------------------------------------
    # Save validation predictions to S3
    # -------------------------------------------------------------------------
    output_columns = []
    if id_column in df_val.columns:
        output_columns.append(id_column)
    output_columns += [target, "prediction"]

    if model_type != "classifier":
        output_columns.append("prediction_std")
        output_columns += [c for c in df_val.columns if c.startswith("q_") or c == "confidence"]

    output_columns += [c for c in df_val.columns if c.endswith("_proba")]

    wr.s3.to_csv(df_val[output_columns], f"{model_metrics_s3_path}/validation_predictions.csv", index=False)

    # -------------------------------------------------------------------------
    # Save model artifacts
    # -------------------------------------------------------------------------
    model_config = {
        "n_continuous": len(continuous_cols),
        "categorical_cardinalities": categorical_cardinalities,
        "hidden_layers": hidden_layers,
        "n_outputs": n_outputs,
        "task": task,
        "dropout": hyperparameters["dropout"],
        "use_batch_norm": hyperparameters["use_batch_norm"],
    }

    for idx, m in enumerate(ensemble_models):
        save_model(m, os.path.join(args.model_dir, f"model_{idx}"), model_config)
    print(f"Saved {len(ensemble_models)} model(s)")

    joblib.dump({"n_ensemble": len(ensemble_models), "n_folds": n_folds}, os.path.join(args.model_dir, "ensemble_metadata.joblib"))

    with open(os.path.join(args.model_dir, "feature_columns.json"), "w") as f:
        json.dump(orig_features, f)

    with open(os.path.join(args.model_dir, "category_mappings.json"), "w") as f:
        json.dump(category_mappings, f)

    with open(os.path.join(args.model_dir, "feature_metadata.json"), "w") as f:
        json.dump({"continuous_cols": continuous_cols, "categorical_cols": categorical_cols}, f)

    with open(os.path.join(args.model_dir, "categorical_impute.json"), "w") as f:
        json.dump(cat_impute_values, f)

    with open(os.path.join(args.model_dir, "hyperparameters.json"), "w") as f:
        json.dump(hyperparameters, f, indent=2)

    scaler.save(os.path.join(args.model_dir, "scaler.joblib"))

    if label_encoder:
        joblib.dump(label_encoder, os.path.join(args.model_dir, "label_encoder.joblib"))

    if model_type != "classifier":
        save_uq_models(uq_models, uq_metadata, args.model_dir)

    print(f"\nModel training complete! Artifacts saved to {args.model_dir}")
