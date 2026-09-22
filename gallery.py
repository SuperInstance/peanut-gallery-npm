"""
Peanut Gallery: Multi-model adversarial creativity.

Casey (2026-09-22): "this also allows for creating madlibs-like setups but on a
higher-abstraction for letting models fill in setups from other models in an effort
to outwit and break and find edges to the others paradigms and log in a GAN game
for many different uses with JEV and JEPA as helpers and peanut gallery"

The pattern:
1. Producer A generates an output
2. Critics B, C, D watch and produce feedback
3. Producer A revises
4. JEV + JEPA vote on which round is best
5. The winning round is canonized

This is "the peanut gallery" — a vocal, opinionated audience that heckles
from the cheap seats, but in AI form.
"""
from __future__ import annotations
import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Optional


# === FNV-1a for prev_hash chain ===
FNV_OFFSET = 0xcbf29ce484222325
FNV_PRIME = 0x100000001b3


def fnv1a_64(text: str) -> str:
    h = FNV_OFFSET
    for byte in text.encode('utf-8'):
        h ^= byte
        h = (h * FNV_PRIME) & 0xffffffffffffffff
    return f"0x{h:016x}"


# === LLM dispatch ===
def call_llm(model: str, prompt: str, max_tokens: int = 1500, temperature: float = 0.7) -> str:
    """Dispatch to whichever LLM by name."""
    if model == 'qwen':
        return _call_openai_compat(
            'https://api.deepinfra.com/v1/openai/chat/completions',
            'DEEPINFRA_TOKEN',
            {'model': 'Qwen/Qwen3-235B-A22B-Instruct-2507', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature},
        )
    elif model == 'deepseek':
        return _call_openai_compat(
            'https://api.deepseek.com/v1/chat/completions',
            'DEEPSEEK_TOKEN',
            {'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature},
        )
    elif model == 'kimi':
        return _call_openai_compat(
            'https://api.deepinfra.com/v1/openai/chat/completions',
            'DEEPINFRA_TOKEN',
            {'model': 'moonshotai/Kimi-K2.6', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature},
        )
    elif model == 'groq':
        return _call_openai_compat(
            'https://api.groq.com/openai/v1/chat/completions',
            'GROQ_TOKEN',
            {'model': 'llama-3.3-70b-versatile', 'messages': [{'role': 'user', 'content': prompt}], 'max_tokens': max_tokens, 'temperature': temperature},
        )
    elif model == 'gemini':
        return _call_gemini(prompt, max_tokens, temperature)
    else:
        raise ValueError(f'Unknown model: {model}')


def _call_openai_compat(url: str, env_key: str, payload: dict) -> str:
    req = json.dumps(payload).encode()
    http_req = urllib.request.Request(
        url,
        data=req,
        headers={'Authorization': f'Bearer {os.environ[env_key]}', 'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(http_req, timeout=60) as r:
        return json.loads(r.read())['choices'][0]['message']['content']


def _call_gemini(prompt: str, max_tokens: int, temperature: float) -> str:
    # Gemini uses a different API
    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={os.environ["GEMINI_TOKEN"]}'
    payload = {
        'contents': [{'parts': [{'text': prompt}]}],
        'generationConfig': {'maxOutputTokens': max_tokens, 'temperature': temperature},
    }
    req = json.dumps(payload).encode()
    http_req = urllib.request.Request(url, data=req, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(http_req, timeout=60) as r:
        return json.loads(r.read())['candidates'][0]['content']['parts'][0]['text']


def call_jev(state: str, questions: dict) -> dict:
    req = json.dumps({'model': 'jev-latest', 'state': state, 'questions': questions}).encode()
    http_req = urllib.request.Request(
        'https://api.typesafe.ai/v1/systemone',
        data=req,
        headers={'Authorization': f'Bearer {os.environ["TYPESAFEAI_KEY"]}', 'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(http_req, timeout=60) as r:
        return json.loads(r.read())


# === Substrate cell ===
@dataclass
class GalleryCell:
    cell_id: str
    round_num: int
    producer: str
    prev_hash: str = '0x0000000000000000'
    output: str = ''
    critiques: list = field(default_factory=list)
    jev_score: float = 0.0
    metadata: dict = field(default_factory=dict)
    
    def hash(self) -> str:
        return fnv1a_64(f'{self.cell_id}|{self.prev_hash}|{self.output}')


@dataclass
class PeanutGallery:
    """The peanut gallery itself — runs the adversarial loop."""
    prompt: str
    producer: str = 'qwen'  # Initial producer
    critics: tuple = ('deepseek', 'kimi', 'groq')  # The gallery
    max_rounds: int = 5
    quality_threshold: float = 9.0
    cells: list = field(default_factory=list)
    
    def run(self) -> dict:
        """Run the full adversarial loop."""
        prev_hash = '0x0000000000000000'
        
        for round_num in range(1, self.max_rounds + 1):
            print(f'\n=== ROUND {round_num} ===')
            
            # 1. Producer generates (or revises)
            if round_num == 1:
                cell = self._initial_producer_round(round_num, prev_hash)
            else:
                cell = self._revise_round(round_num, prev_hash)
            
            # 2. Critics watch
            for critic in self.critics:
                feedback = self._critic_round(critic, cell)
                cell.critiques.append(feedback)
                print(f'  {critic} says: "{feedback.get("summary", "")[:80]}"')
            
            # 3. JEV scores
            jev_score = self._jev_score(cell)
            cell.jev_score = jev_score
            print(f'  JEV score: {jev_score:.2f}/10')
            
            self.cells.append(cell)
            prev_hash = cell.hash()
            
            # 4. Check if quality threshold met
            if jev_score >= self.quality_threshold:
                print(f'  ✓ Quality threshold met ({jev_score:.1f} >= {self.quality_threshold}). Stopping.')
                break
        
        return self.report()
    
    def _initial_producer_round(self, round_num: int, prev_hash: str) -> GalleryCell:
        """First round: producer generates from scratch."""
        prompt = f"""{self.prompt}

Generate your best output. The peanut gallery will critique it next."""
        
        output = call_llm(self.producer, prompt, max_tokens=1000, temperature=0.8)
        return GalleryCell(
            cell_id=f'gallery-{round_num:02d}',
            round_num=round_num,
            producer=self.producer,
            prev_hash=prev_hash,
            output=output,
            metadata={'round_type': 'initial'},
        )
    
    def _critic_round(self, critic: str, cell: GalleryCell) -> dict:
        """A critic watches the output and provides feedback."""
        prompt = f"""You are a critic in the peanut gallery. Your job: find what's wrong, what could be better, what edge cases are missed.

PROMPT: {self.prompt}

OUTPUT TO CRITIQUE:
{cell.output}

Reply with JSON:
{{
  "summary": "1-sentence summary of your critique",
  "issues": ["issue 1", "issue 2", ...],
  "suggestions": ["suggestion 1", "suggestion 2", ...],
  "score": 0-10
}}
"""
        try:
            response = call_llm(critic, prompt, max_tokens=500, temperature=0.5)
            m = re.search(r'\{[\s\S]*\}', response)
            if m:
                return json.loads(m.group())
        except Exception as e:
            return {'summary': f'critique failed: {e}', 'issues': [], 'suggestions': [], 'score': 5}
        return {'summary': 'no critique', 'issues': [], 'suggestions': [], 'score': 5}
    
    def _revise_round(self, round_num: int, prev_hash: str) -> GalleryCell:
        """Subsequent rounds: producer revises based on gallery feedback."""
        prev_cell = self.cells[-1]
        
        # Aggregate feedback
        all_issues = []
        all_suggestions = []
        for c in prev_cell.critiques:
            all_issues.extend(c.get('issues', []))
            all_suggestions.extend(c.get('suggestions', []))
        
        feedback_summary = '\n'.join(f'- {s}' for s in all_suggestions[:5]) if all_suggestions else 'No specific suggestions'
        issues_summary = '\n'.join(f'- {i}' for i in all_issues[:5]) if all_issues else 'No specific issues'
        
        prompt = f"""You are revising your previous output based on the gallery's feedback.

PROMPT: {self.prompt}

PREVIOUS OUTPUT (round {prev_cell.round_num}):
{prev_cell.output}

ISSUES RAISED:
{issues_summary}

SUGGESTIONS:
{feedback_summary}

REVISED OUTPUT (improve on all feedback):"""
        
        output = call_llm(self.producer, prompt, max_tokens=1000, temperature=0.7)
        return GalleryCell(
            cell_id=f'gallery-{round_num:02d}',
            round_num=round_num,
            producer=self.producer,
            prev_hash=prev_hash,
            output=output,
            metadata={'round_type': 'revision', 'feedback_round': prev_cell.round_num},
        )
    
    def _jev_score(self, cell: GalleryCell) -> float:
        """JEV scores the cell against the prompt."""
        try:
            response = call_jev(cell.output, {
                'quality': {
                    'type': 'score',
                    'instructions': f'How well does this output address the prompt: "{self.prompt}"? 0=irrelevant, 1=adequate, 2=excellent',
                    'criteria': ['irrelevant', 'adequate', 'excellent'],
                },
            })
            return response['answers']['quality']['score'] * 5  # 0-2 → 0-10
        except Exception:
            # Fallback: average critic scores
            scores = [c.get('score', 5) for c in cell.critiques]
            return sum(scores) / len(scores) if scores else 5
    
    def report(self) -> dict:
        return {
            'prompt': self.prompt,
            'producer': self.producer,
            'critics': list(self.critics),
            'rounds': len(self.cells),
            'final_score': self.cells[-1].jev_score if self.cells else 0,
            'final_output': self.cells[-1].output if self.cells else '',
            'cells': [
                {
                    'cell_id': c.cell_id,
                    'round': c.round_num,
                    'producer': c.producer,
                    'prev_hash': c.prev_hash,
                    'hash': c.hash(),
                    'output_preview': c.output[:200],
                    'critiques': c.critiques,
                    'jev_score': c.jev_score,
                }
                for c in self.cells
            ],
        }


# === Demo ===
def demo():
    gallery = PeanutGallery(
        prompt='Write a 4-line poem about the substrate that contains the whole universe.',
        producer='qwen',
        critics=('deepseek', 'kimi', 'groq'),
        max_rounds=3,
        quality_threshold=8.5,
    )
    result = gallery.run()
    print('\n=== FINAL OUTPUT ===')
    print(result['final_output'][:600])
    print(f'\nFinal JEV score: {result["final_score"]:.2f}/10')
    return result


if __name__ == '__main__':
    demo()
