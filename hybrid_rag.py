import os
import sys

try:
    from llama_cpp import Llama
except ImportError:
    print("CRITICAL: llama-cpp-python not installed. Cannot run real LLM.")
    sys.exit(1)


class HybridLlmEngine:
    def __init__(self, model_path="./models/mistral-7b-instruct.Q4_K_M.gguf"):
        self.model = None

        if not os.path.exists(model_path):
            print(f"FATAL: LLM Model not found at: {model_path}")
            print("Please download 'mistral-7b-instruct.Q4_K_M.gguf' and put it in ./models/")
            sys.exit(1)

        print(f"Loading Llama Model...")
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_gpu_layers=-1,
                verbose=False
            )
        except Exception as e:
            print(f"FATAL: Failed to load GGUF model. {e}")
            sys.exit(1)

    def generate_explanation(self, forecast_result, context_docs):
        prompt = f"""[INST] You are a sales analyst.

        FORECAST DATA:
        - Prediction: ${forecast_result.prediction:,.2f}
        - Confidence: {forecast_result.confidence_score:.1f}%
        - Breakdown: {forecast_result.breakdown}

        HISTORICAL CONTEXT:
        {chr(10).join(['- ' + doc for doc in context_docs])}

        Task: Explain this forecast using the context provided.
        [/INST]
        """

        output = self.model(
            prompt,
            max_tokens=512,
            stop=["[/INST]"],
            temperature=0.7
        )
        return output['choices'][0]['text']