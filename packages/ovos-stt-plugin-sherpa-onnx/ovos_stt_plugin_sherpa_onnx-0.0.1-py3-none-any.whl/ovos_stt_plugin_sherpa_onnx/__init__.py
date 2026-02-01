import os.path
import shutil
import tarfile
import urllib.request
from typing import Optional

import sherpa_onnx as so
from ovos_plugin_manager.templates.stt import STT
from ovos_plugin_manager.utils.audio import AudioData
from ovos_utils import classproperty
from ovos_utils.xdg_utils import XDG_CACHE_HOME


class SherpaOnnxSTT(STT):
    DOWNLOAD_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/{model_id}.tar.bz2"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_model()

    def _load_model(self):
        provider = self.config.get("provider", "cpu")
        model_type = self.config.get("model_type", "transducer")
        model_id = self.config.get("model")
        if model_id:
            model_dir = self.download(model_id)
        else:
            model_dir = None  # user is passing explicit paths to model files

        # Load model
        if model_type == "transducer":
            encoder = self.config.get("encoder", "encoder.onnx")
            decoder = self.config.get("decoder", "decoder.onnx")
            joiner = self.config.get("joiner", "joiner.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                encoder = f"{model_dir}/{encoder}"
                decoder = f"{model_dir}/{decoder}"
                joiner = f"{model_dir}/{joiner}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(encoder), "encoder model missing"
            assert os.path.isfile(decoder), "decoder model missing"
            assert os.path.isfile(joiner), "joiner model missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_transducer(
                encoder=encoder,
                decoder=decoder,
                joiner=joiner,
                tokens=tokens,
                provider=provider,
                model_type=model_type
            )

        elif model_type == "moonshine":
            encoder = self.config.get("encoder", "encoder.onnx")
            uncached_decoder = self.config.get("uncached_decoder", "uncached_decoder.onnx")
            cached_decoder = self.config.get("cached_decoder", "cached_decoder.onnx")
            preprocessor = self.config.get("preprocessor", "preprocessor.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                encoder = f"{model_dir}/{encoder}"
                uncached_decoder = f"{model_dir}/{uncached_decoder}"
                cached_decoder = f"{model_dir}/{cached_decoder}"
                tokens = f"{model_dir}/{tokens}"
                preprocessor = f"{model_dir}/{preprocessor}"

            assert os.path.isfile(preprocessor), "preprocessor model missing"
            assert os.path.isfile(encoder), "encoder model missing"
            assert os.path.isfile(uncached_decoder), "uncached_decoder model missing"
            assert os.path.isfile(cached_decoder), "cached_decoder model missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_moonshine(
                debug=True,
                preprocessor=preprocessor,
                encoder=encoder,
                uncached_decoder=uncached_decoder,
                cached_decoder=cached_decoder,
                tokens=tokens
            )

        elif model_type == "tdnn-ctc":
            model = self.config.get("model_file", "model.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                model = f"{model_dir}/{model}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(model), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_tdnn_ctc(
                model=model,
                tokens=tokens
            )

        elif model_type == "wenet-ctc":
            model = self.config.get("model_file", "model.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                model = f"{model_dir}/{model}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(model), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_wenet_ctc(
                model=model,
                tokens=tokens
            )

        elif model_type == "paraformer":
            model = self.config.get("model_file", "model.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                model = f"{model_dir}/{model}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(model), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_paraformer(
                paraformer=model,
                tokens=tokens
            )

        elif model_type == "whisper":
            encoder = self.config.get("encoder", "encoder.onnx")
            decoder = self.config.get("decoder", "decoder.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                encoder = f"{model_dir}/{encoder}"
                decoder = f"{model_dir}/{decoder}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(encoder), "model file missing"
            assert os.path.isfile(decoder), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_whisper(
                encoder=encoder,
                decoder=decoder,
                tokens=tokens
            )

        elif model_type == "fire-red-asr":
            encoder = self.config.get("encoder", "encoder.onnx")
            decoder = self.config.get("decoder", "decoder.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                encoder = f"{model_dir}/{encoder}"
                decoder = f"{model_dir}/{decoder}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(encoder), "model file missing"
            assert os.path.isfile(decoder), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_fire_red_asr(
                encoder=encoder,
                decoder=decoder,
                tokens=tokens
            )

        elif model_type == "nemo-canary":
            encoder = self.config.get("encoder", "encoder.onnx")
            decoder = self.config.get("decoder", "decoder.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                encoder = f"{model_dir}/{encoder}"
                decoder = f"{model_dir}/{decoder}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(encoder), "model file missing"
            assert os.path.isfile(decoder), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_nemo_canary(
                encoder=encoder,
                decoder=decoder,
                tokens=tokens
            )

        elif model_type == "nemo-ctc":
            model = self.config.get("model_file", "model.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                model = f"{model_dir}/{model}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(model), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_nemo_ctc(
                model=model,
                tokens=tokens
            )

        elif model_type == "zipformer-ctc":
            model = self.config.get("model_file", "model.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                model = f"{model_dir}/{model}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(model), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_zipformer_ctc(
                model=model,
                tokens=tokens
            )

        elif model_type == "omnilingual-asr-ctc":
            model = self.config.get("model_file", "model.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                model = f"{model_dir}/{model}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(model), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_omnilingual_asr_ctc(
                model=model,
                tokens=tokens
            )

        elif model_type == "telespeech-ctc":
            model = self.config.get("model_file", "model.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                model = f"{model_dir}/{model}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(model), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_telespeech_ctc(
                model=model,
                tokens=tokens
            )

        elif model_type == "dolphin-ctc":
            model = self.config.get("model_file", "model.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                model = f"{model_dir}/{model}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(model), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_dolphin_ctc(
                model=model,
                tokens=tokens
            )

        elif model_type == "medasr-ctc":
            model = self.config.get("model_file", "model.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                model = f"{model_dir}/{model}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(model), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_medasr_ctc(
                model=model,
                tokens=tokens
            )

        elif model_type == "moonshine":
            encoder = self.config.get("encoder", "encoder.onnx")
            uncached_decoder = self.config.get("uncached_decoder", "uncached_decoder.onnx")
            cached_decoder = self.config.get("cached_decoder", "cached_decoder.onnx")
            preprocessor = self.config.get("preprocessor", "preprocessor.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                encoder = f"{model_dir}/{encoder}"
                uncached_decoder = f"{model_dir}/{uncached_decoder}"
                cached_decoder = f"{model_dir}/{cached_decoder}"
                tokens = f"{model_dir}/{tokens}"
                preprocessor = f"{model_dir}/{preprocessor}"

            assert os.path.isfile(preprocessor), "preprocessor model missing"
            assert os.path.isfile(encoder), "encoder model missing"
            assert os.path.isfile(uncached_decoder), "uncached_decoder model missing"
            assert os.path.isfile(cached_decoder), "cached_decoder model missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_moonshine(
                debug=True,
                preprocessor=preprocessor,
                encoder=encoder,
                uncached_decoder=uncached_decoder,
                cached_decoder=cached_decoder,
                tokens=tokens
            )

        elif model_type == "sense-voice":
            model = self.config.get("model_file", "model.onnx")
            tokens = self.config.get("tokens", "tokens.txt")
            if model_dir:  # model downloaded to cache
                model = f"{model_dir}/{model}"
                tokens = f"{model_dir}/{tokens}"

            assert os.path.isfile(model), "model file missing"
            assert os.path.isfile(tokens), "tokens missing"

            self.recognizer = so.OfflineRecognizer.from_sense_voice(
                model=model,
                tokens=tokens
            )

        elif model_type == "funasr-nano":
            llm = self.config.get("llm", "llm.onnx")
            encoder_adaptor = self.config.get("encoder_adaptor", "encoder_adaptor.onnx")
            embedding = self.config.get("embedding", "embedding.onnx")
            tokenizer = self.config.get("tokenizer", "Qwen3-0.6B")

            if model_dir:  # model downloaded to cache
                llm = f"{model_dir}/{llm}"
                embedding = f"{model_dir}/{embedding}"
                encoder_adaptor = f"{model_dir}/{encoder_adaptor}"
                tokenizer = f"{model_dir}/{tokenizer}"

            assert os.path.isfile(llm), "file missing"
            assert os.path.isfile(encoder_adaptor), "file missing"
            assert os.path.isfile(embedding), "file missing"
            assert os.path.isdir(tokenizer), "file missing"

            self.recognizer = so.OfflineRecognizer.from_funasr_nano(
                encoder_adaptor=encoder_adaptor,
                llm=llm,
                embedding=embedding,
                tokenizer=tokenizer,
            )

        else:
            raise ValueError(f"unknown model type: {model_type}")

    def download(self, model_id):
        url = self.DOWNLOAD_URL.format(model_id=model_id)
        cache_dir = os.path.join(XDG_CACHE_HOME, "sherpa-onnx")
        model_dir = os.path.join(cache_dir, model_id)
        if os.path.isdir(model_dir):
            return model_dir
        os.makedirs(cache_dir, exist_ok=True)
        try:
            # Download/extract to cache dir.
            # We assume that the .tar.bz2 contains a directory named after
            # the model id.
            with urllib.request.urlopen(url) as response:
                with tarfile.open(fileobj=response, mode="r|bz2") as tar:
                    for member in tar:
                        tar.extract(member, path=cache_dir)
        except Exception:
            # Delete directory so we'll download again next time
            shutil.rmtree(model_dir, ignore_errors=True)
            raise
        return model_dir

    @classproperty
    def available_languages(cls) -> set:
        return set()

    def execute(self, audio: AudioData, language: Optional[str] = None):
        """
        Transcribes the provided audio using the configured model and language.

        Parameters:
            audio (AudioData): Audio input to be processed.
            language (Optional[str]): Language code to use for transcription; if omitted, the instance's current language is used.

        Returns:
            transcription (str): Final recognized text for the processed audio.
        """
        stream = self.recognizer.create_stream()
        stream.accept_waveform(audio.sample_rate, audio.get_np_float32())
        self.recognizer.decode_stream(stream)
        return stream.result.text


# TODO - streaming STT
#
# so.OnlineRecognizer.from_paraformer()
# so.OnlineRecognizer.from_transducer()
# so.OnlineRecognizer.from_nemo_ctc()
# so.OnlineRecognizer.from_wenet_ctc()
# so.OnlineRecognizer.from_t_one_ctc()
# so.OnlineRecognizer.from_zipformer2_ctc(

if __name__ == "__main__":
    config = {
        "lang": "en",
        "model": "sherpa-onnx-nemo-fast-conformer-transducer-en-de-es-fr-14288",
        "model_type": "transducer",
        "encoder": "encoder.onnx",
        "decoder": "decoder.onnx",
        "joiner": "joiner.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-moonshine-base-en-int8",
        "model_type": "moonshine",
        "encoder": "encode.int8.onnx",
        "uncached_decoder": "uncached_decode.int8.onnx",
        "cached_decoder": "cached_decode.int8.onnx",
        "preprocessor": "preprocess.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09",
        "model_type": "sense-voice",
        "model_file": "model.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-funasr-nano-int8-2025-12-30",
        "model_type": "funasr-nano",
        "llm": "llm.int8.onnx",
        "embedding": "embedding.int8.onnx",
        "encoder_adaptor": "encoder_adaptor.int8.onnx",
        "tokenizer": "Qwen3-0.6B"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-paraformer-en-2024-03-09",
        "model_type": "paraformer",
        "model_file": "model.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "zh",
        "model": "sherpa-onnx-telespeech-ctc-int8-zh-2024-06-04",
        "model_type": "telespeech-ctc",
        "model_file": "model.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-dolphin-base-ctc-multi-lang-int8-2025-04-02",
        "model_type": "dolphin-ctc",
        "model_file": "model.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-medasr-ctc-en-int8-2025-12-25",
        "model_type": "medasr-ctc",
        "model_file": "model.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-omnilingual-asr-1600-languages-1B-ctc-int8-2025-11-12",
        "model_type": "omnilingual-asr-ctc",
        "model_file": "model.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-zipformer-ctc-en-2023-10-02",
        "model_type": "zipformer-ctc",
        "model_file": "model.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-nemo-ctc-en-citrinet-512",
        "model_type": "nemo-ctc",
        "model_file": "model.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-nemo-canary-180m-flash-en-es-de-fr-int8",
        "model_type": "nemo-canary",
        "encoder": "encoder.int8.onnx",
        "decoder": "decoder.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-whisper-turbo",
        "model_type": "whisper",
        "encoder": "turbo-encoder.int8.onnx",
        "decoder": "turbo-decoder.int8.onnx",
        "tokens": "turbo-tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-fire-red-asr-large-zh_en-2025-02-16",
        "model_type": "fire-red-asr",
        "encoder": "encoder.int8.onnx",
        "decoder": "decoder.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-tdnn-yesno",
        "model_type": "tdnn-ctc",
        "model_file": "model-epoch-14-avg-2.int8.onnx",
        "tokens": "tokens.txt"
    }
    config = {
        "lang": "en",
        "model": "sherpa-onnx-en-wenet-librispeech",
        "model_type": "wenet-ctc",
        "model_file": "model.onnx",
        "tokens": "tokens.txt"
    }

    config = {
        "lang": "en",
        "model": "sherpa-onnx-zipformer-en-libriheavy-20230830-large-punct-case",
        "model_type": "transducer",
        "encoder": "encoder-epoch-16-avg-2.int8.onnx",
        "decoder": "decoder-epoch-16-avg-2.int8.onnx",
        "joiner": "joiner-epoch-16-avg-2.int8.onnx",
        "tokens": "tokens.txt"
    }

    b = SherpaOnnxSTT(config)

    eu = "/home/miro/PycharmProjects/ovos-stt-plugin-vosk/jfk.wav"
    audio = AudioData.from_file(eu)

    a = b.execute(audio, language="en")
    print(a)
