import sys
import os
import argparse
import numpy as np
import pandas as pd

from chronoforge_rag import RAGQuery, LLMConfig
from rag_pipeline import RAGPipelineBuilder
from forecasting_engine import HybridForecastingEngine
from hybrid_rag import HybridLlmEngine


def load_sales_data(filepath):
    if not os.path.exists(filepath):
        print(f"FATAL: Data file {filepath} missing.")
        sys.exit(1)

    df = pd.read_csv(filepath)
    col = 'sales_value' if 'sales_value' in df.columns else df.columns[1]
    return df[col].tail(30).values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--kb", default="./kb")
    parser.add_argument("--data", default="sales_data.csv")
    parser.add_argument("--model", default="./models/mistral-7b-instruct.Q4_K_M.gguf")
    args = parser.parse_args()

    print("ChronoForge Pulse (Strict Real-Data Mode)")

    forecaster = HybridForecastingEngine()
    llm_engine = HybridLlmEngine(model_path=args.model)

    if not os.path.exists(args.kb):
        print(f"FATAL: Knowledge Base missing at {args.kb}")
        print("Run 'build_knowledge_base.py ./kb sales_data.csv' first.")
        sys.exit(1)

    print(f"[System] Loading Knowledge Base...")
    pipeline_builder = RAGPipelineBuilder()
    pipeline_builder.with_llm_config(LLMConfig(provider="mock"))

    pipeline = pipeline_builder.build_with_knowledge_base(args.kb)
    knowledge_base = pipeline.get_knowledge_base()

    while True:
        try:
            query = input("\nQuery> ").strip()
            if query.lower() in ['exit', 'quit']:
                break

            # Forecast
            forecast_result = None
            if any(k in query.lower() for k in ["predict", "forecast", "sales"]):
                print("Running Real Ensemble Models...")
                recent_data = load_sales_data(args.data)
                forecast_result = forecaster.generate_forecast(recent_data)
                print(f"Prediction: ${forecast_result.prediction:,.2f}")

            # RAG Search
            context_docs = []
            print("Searching Vector Database...")
            search_results = knowledge_base.search(RAGQuery(query_text=query))

            for res in search_results:
                s = res.scenario
                context_docs.append(f"{s.date}: {s.description} [Sales: {s.sales_value}]")

            # LLM Generation
            print("Mistral 7B Thinking...")
            if forecast_result:
                response = llm_engine.generate_explanation(forecast_result, context_docs)
            else:
                prompt = f"[INST] Context: {context_docs} Question: {query} [/INST]"
                output = llm_engine.model(prompt, max_tokens=512)
                response = output['choices'][0]['text']

            print(f"\n{response}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()