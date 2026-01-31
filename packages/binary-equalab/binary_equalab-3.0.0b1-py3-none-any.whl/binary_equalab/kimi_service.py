
import os
import json
import requests
from typing import List, Dict, Optional, Generator
from rich.console import Console

console = Console()

class KimiService:
    """Service to interact with Kimi K2 (Moonshot AI) via Direct API"""
    
    def __init__(self):
        # Priority: Env Var > .env File > Config File
        self.api_key = os.getenv('KIMI_API_KEY')
        
        # Manually load .env if not found in environment
        if not self.api_key:
            try:
                env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
                if os.path.exists(env_path):
                    with open(env_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip().startswith('KIMI_API_KEY='):
                                self.api_key = line.strip().split('=', 1)[1].strip('"\'')
                                os.environ['KIMI_API_KEY'] = self.api_key
                                break
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load .env file: {e}[/yellow]")

        self.base_url = 'https://api.moonshot.cn/v1'
        self.model = 'moonshot-v1-128k' # Using 128k model as K2 proxy
        
    def set_api_key(self, key: str):
        self.api_key = key
        # In a real app, save this to a config file
        os.environ['KIMI_API_KEY'] = key

    def _get_headers(self):
        if not self.api_key:
            raise ValueError("KIMI_API_KEY not configured. Run 'export KIMI_API_KEY=sk-...'")
        return {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
        """Send message to Kimi"""
        try:
            payload = {
                'model': self.model,
                'messages': messages,
                'temperature': temperature,
            }
            response = requests.post(f'{self.base_url}/chat/completions', headers=self._get_headers(), json=payload)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error connecting to Kimi AI: {str(e)}"

    def solve_math_problem(self, problem: str, show_steps: bool = True) -> Dict[str, any]:
        """
        Resolver problema matemático con razonamiento paso a paso.
        Retorna un diccionario estructurado.
        """
        system_prompt = f"""Eres un asistente matemático experto de Aldra's Team (Binary EquaLab AI).

Resuelve el siguiente problema {'mostrando TODOS los pasos' if show_steps else 'directamente'}.

Responde ESTRICTAMENTE en formato JSON con esta estructura:
{{
  "solution": "Respuesta final matemática (LaTeX/texto)",
  "steps": ["Paso 1: ...", "Paso 2: ..."],
  "reasoning": "Explicación breve del enfoque",
  "difficulty": "fácil|medio|difícil",
  "concepts": ["Concepto 1", "Concepto 2"]
}}"""
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': problem}
        ]
        
        response_text = self.chat(messages, temperature=0.3)
        try:
            # Limpiar markdown si el modelo lo incluye (e.g. ```json ... ```)
            cleaned = response_text.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {
                "solution": response_text,
                "steps": ["No se pudo parsear la respuesta estructurada."],
                "reasoning": "Respuesta directa del modelo.",
                "difficulty": "desconocido",
                "concepts": []
            }

    def explain_concept(self, concept: str, level: str = 'intermedio') -> str:
        """Explicación pedagógica de conceptos"""
        system_prompt = f"""Eres un profesor de matemáticas apasionado de Aldra's Team.
        Explica el concepto solicitado para un nivel {level}.
        Usa analogías, claridad y rigor."""
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"Explícame: {concept}"}
        ]
        return self.chat(messages, temperature=0.5)

    def generate_exercises(self, topic: str, count: int = 5, difficulty: str = 'medio') -> List[Dict[str, any]]:
        """Generar ejercicios de práctica"""
        system_prompt = f"""Genera {count} ejercicios de {topic} con dificultad {difficulty}.
        
        Responde ESTRICTAMENTE en formato JSON (Array de objetos):
        [
          {{
            "problem": "Enunciado",
            "solution": "Respuesta",
            "steps": ["Paso 1", "Paso 2"],
            "concepts": ["Concepto A"]
          }}
        ]"""
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': "Genera los ejercicios."}
        ]
        
        response_text = self.chat(messages, temperature=0.7)
        try:
            cleaned = response_text.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return []

# Singleton
kimi_service = KimiService()
