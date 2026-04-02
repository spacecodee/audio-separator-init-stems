import os
from pathlib import Path

APP_DIR = Path(os.getenv("APP_DIR", "/app"))
INPUT_DIR = Path(os.getenv("INPUT_DIR", str(APP_DIR / "input")))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", str(APP_DIR / "output")))
MODEL_DIR = Path(os.getenv("MODEL_DIR", "/root/.cache/audio-separator"))
MODELS_EXPLORER_HTML = APP_DIR / "models-explorer.html"
MODELS_EXPLORER_CSS = APP_DIR / "models-explorer.css"
MODELS_EXPLORER_JS = APP_DIR / "models-explorer.js"
MODELS_EXPLORER_JSON = APP_DIR / "models.json"

for directory in (INPUT_DIR, OUTPUT_DIR, MODEL_DIR):
    directory.mkdir(parents=True, exist_ok=True)

MODELS = {
    # Vocales principales / acapella
    "kim_vocals": "vocals_mel_band_roformer.ckpt",
    "big_beta4": "melband_roformer_big_beta4.ckpt",
    "big_beta5e": "melband_roformer_big_beta5e.ckpt",
    "big_syhft_v1": "MelBandRoformerBigSYHFTV1.ckpt",
    "kim_ft": "mel_band_roformer_kim_ft_unwa.ckpt",
    "kim_ft2": "mel_band_roformer_kim_ft2_unwa.ckpt",
    "kim_ft2_bleedless": "mel_band_roformer_kim_ft2_bleedless_unwa.ckpt",
    "bs_roformer": "model_bs_roformer_ep_317_sdr_12.9755.ckpt",
    "bs_roformer_1296": "model_bs_roformer_ep_368_sdr_12.9628.ckpt",
    "mel_roformer": "model_mel_band_roformer_ep_3005_sdr_11.4360.ckpt",

    # Instrumental
    "inst_duality_v2": "melband_roformer_instvox_duality_v2.ckpt",
    "inst_duality_v1": "melband_roformer_instvoc_duality_v1.ckpt",
    "inst_v2": "melband_roformer_inst_v2.ckpt",
    "inst_v1": "melband_roformer_inst_v1.ckpt",
    "inst_v1e": "melband_roformer_inst_v1e.ckpt",
    "inst_bleedless_v1": "mel_band_roformer_instrumental_bleedless_v1_gabox.ckpt",
    "inst_bleedless_v2": "mel_band_roformer_instrumental_bleedless_v2_gabox.ckpt",
    "inst_bleedless_v3": "mel_band_roformer_instrumental_bleedless_v3_gabox.ckpt",
    "inst_fullness_v3": "mel_band_roformer_instrumental_fullness_v3_gabox.ckpt",
    "inst_instv8": "mel_band_roformer_instrumental_instv8_gabox.ckpt",
    "mdx23c_instvoc_hq2": "MDX23C-8KFFT-InstVoc_HQ_2.ckpt",
    "mdx23c_instvoc_hq": "MDX23C-8KFFT-InstVoc_HQ.ckpt",
    "bs_resurrection_inst": "bs_roformer_instrumental_resurrection_unwa.ckpt",

    # Karaoke / backing vocals
    "mel_karaoke": "mel_band_roformer_karaoke_aufr33_viperx_sdr_10.1956.ckpt",
    "mel_karaoke_gabox": "mel_band_roformer_karaoke_gabox.ckpt",
    "mel_karaoke_gabox_v2": "mel_band_roformer_karaoke_gabox_v2.ckpt",
    "mel_karaoke_becruily": "mel_band_roformer_karaoke_becruily.ckpt",

    # Backing vocals extractor
    "bve_1": "UVR-BVE-4B_SN-44100-1.pth",
    "bve_2": "UVR-BVE-4B_SN-44100-2.pth",

    # Coros / masculino-femenino
    "chorus_male_female": "model_chorus_bs_roformer_ep_267_sdr_24.1275.ckpt",
    "male_female_aufr33": "bs_roformer_male_female_by_aufr33_sdr_7.2889.ckpt",

    # Multi-stem 4 pistas
    "htdemucs_ft": "htdemucs_ft.yaml",
    "htdemucs": "htdemucs.yaml",
    "hdemucs_mmi": "hdemucs_mmi.yaml",

    # Multi-stem 6 pistas
    "htdemucs_6s": "htdemucs_6s.yaml",

    # Bateria detallada
    "drumsep": "MDX23C-DrumSep-aufr33-jarredou.ckpt",

    # Drum-bass
    "drum_bass_sep": "model_bs_roformer_ep_937_sdr_10.5309.ckpt",

    # Vientos
    "woodwinds": "17_HP-Wind_Inst-UVR.pth",

    # De-reverb
    "dereverb_mel": "dereverb_mel_band_roformer_anvuew_sdr_19.1729.ckpt",
    "dereverb_mel_la": "dereverb_mel_band_roformer_less_aggressive_anvuew_sdr_18.8050.ckpt",
    "dereverb_mel_mono": "dereverb_mel_band_roformer_mono_anvuew.ckpt",
    "dereverb_mel_big": "dereverb_big_mbr_ep_362.ckpt",
    "dereverb_mel_sbig": "dereverb_super_big_mbr_ep_346.ckpt",
    "dereverb_bs": "deverb_bs_roformer_8_384dim_10depth.ckpt",
    "dereverb_vr": "UVR-De-Reverb-aufr33-jarredou.pth",
    "dereverb_mdx23c": "MDX23C-De-Reverb-aufr33-jarredou.ckpt",

    # De-reverb + de-echo
    "dereverb_echo": "dereverb-echo_mel_band_roformer_sdr_13.4843_v2.ckpt",
    "dereverb_echo_fused": "dereverb_echo_mbr_fused.ckpt",
    "dereverb_echo_v1": "dereverb-echo_mel_band_roformer_sdr_10.0169.ckpt",
    "deecho_dereverb_vr": "UVR-DeEcho-DeReverb.pth",

    # De-echo
    "deecho_aggressive": "UVR-De-Echo-Aggressive.pth",
    "deecho_normal": "UVR-De-Echo-Normal.pth",
    "reverb_hq": "Reverb_HQ_By_FoxJoy.onnx",

    # De-noise
    "denoise": "UVR-DeNoise.pth",
    "denoise_lite": "UVR-DeNoise-Lite.pth",
    "denoise_mel_aufr33": "denoise_mel_band_roformer_aufr33_sdr_27.9959.ckpt",
    "denoise_mel_aggr": "denoise_mel_band_roformer_aufr33_aggr_sdr_27.9768.ckpt",

    # Crowd / audiencia
    "crowd_mel": "mel_band_roformer_crowd_aufr33_viperx_sdr_8.7144.ckpt",
    "crowd_mdx": "UVR-MDX-NET_Crowd_HQ_1.onnx",

    # Aspiracion / breath
    "aspiration": "aspiration_mel_band_roformer_sdr_18.9845.ckpt",
    "aspiration_la": "aspiration_mel_band_roformer_less_aggr_sdr_18.1201.ckpt",

    # Bleed suppressor
    "bleed_suppressor": "mel_band_roformer_bleed_suppressor_v1.ckpt",

    # Resurrection
    "vocals_resurrection": "bs_roformer_vocals_resurrection_unwa.ckpt",
    "vocals_revive": "bs_roformer_vocals_revive_unwa.ckpt",
}

VALID_OUTPUT_FORMATS = {"wav", "flac", "mp3"}
GUITAR_SOURCE_MODELS = {"htdemucs_6s"}
GUITAR_DEREVERB_MODELS = {
    "dereverb_mel",
    "dereverb_mel_la",
    "dereverb_mel_mono",
    "dereverb_mel_big",
    "dereverb_mel_sbig",
    "dereverb_bs",
    "dereverb_vr",
    "dereverb_mdx23c",
    "dereverb_echo",
    "dereverb_echo_fused",
    "dereverb_echo_v1",
    "deecho_dereverb_vr",
}
VOCAL_RECONSTRUCT_MODELS = {"vocals_resurrection", "vocals_revive"}
VOCAL_GENDER_SPLIT_MODELS = {"chorus_male_female", "male_female_aufr33"}
DEREVERB_MODELS = set(GUITAR_DEREVERB_MODELS)
DEECHO_MODELS = {
    "deecho_normal",
    "deecho_aggressive",
    "dereverb_echo",
    "dereverb_echo_fused",
    "dereverb_echo_v1",
    "deecho_dereverb_vr",
}
COMBINED_DEREVERB_DEECHO_MODELS = {
    "dereverb_echo",
    "dereverb_echo_fused",
    "dereverb_echo_v1",
    "deecho_dereverb_vr",
}

DEFAULT_PIPELINE_MODELS = {"step1": "mel_roformer", "step2": "mel_karaoke", "step3": "dereverb_mel"}
DEFAULT_GUITAR_PIPELINE_MODELS = {"step1": "htdemucs_6s", "step2": "dereverb_mel"}
DEFAULT_VOCALS_RECONSTRUCT_MODELS = {"step1": "mel_roformer", "step2": "vocals_resurrection"}
DEFAULT_VOCALS_MALE_FEMALE_MODELS = {"step1": "mel_roformer", "step2": "chorus_male_female"}
DEFAULT_EFFECTS_MODELS = {
    "dereverb": "dereverb_mel",
    "deecho": "deecho_normal",
    "dereverb_deecho": {
        "combined_model": "dereverb_echo",
        "fallback_dereverb_model": "dereverb_mel",
        "fallback_deecho_model": "deecho_normal",
    },
}
PRELOAD_MODELS = ["mel_roformer", "mel_karaoke", "dereverb_mel", "deecho_normal", "dereverb_echo"]
