"""
Local clip scoring system - detects funny moments and high-energy segments
No API calls needed - 100% local analysis
"""
import logging
import re
from typing import List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class LocalClipScorer:
    """Scores video segments to find the best moments (jokes, energy, engagement)"""

    def __init__(self):
        # French funny/energy keywords with weights
        self.energy_keywords = {
            # Laughs and reactions
            'mdr': 30, 'lol': 30, 'ptdr': 35, 'xd': 25, 'haha': 25, 'hihi': 20,
            'rire': 25, 'rigole': 25, 'mort': 30, 'grave': 20,

            # Exclamations
            'incroyable': 25, 'dingue': 30, 'fou': 30, 'ouf': 35, 'chaud': 25,
            'énorme': 30, 'putain': 20, 'merde': 20, 'bordel': 20,
            'carrément': 20, 'franchement': 15, 'sérieux': 20,

            # Positive energy
            'génial': 25, 'super': 20, 'top': 25, 'excellent': 25,
            'magnifique': 20, 'parfait': 20, 'cool': 20, 'stylé': 25,

            # Surprise/shock
            'quoi': 15, 'comment': 15, 'attend': 20, 'regarde': 20,
            'écoute': 15, 'imagine': 25, 'crois': 15,

            # Storytelling
            'histoire': 15, 'truc': 10, 'machin': 10, 'moment': 15,
            'fois': 10, 'jour': 10, 'type': 15, 'mec': 15,

            # Intensity
            'trop': 15, 'vraiment': 10, 'complètement': 15, 'totalement': 15,
            'hyper': 20, 'ultra': 20, 'mega': 25, 'grave': 15,
        }

        # Question words (jokes often use Q&A format)
        self.question_words = [
            'pourquoi', 'comment', 'quoi', 'qui', 'quand', 'où',
            'combien', 'quel', 'quelle', 'est-ce que'
        ]

        # Negative words (avoid too much negativity)
        self.negative_words = {
            'triste': -15, 'nul': -10, 'chiant': -15, 'ennuyeux': -20,
            'mauvais': -10, 'horrible': -15, 'terrible': -10,
            'pourri': -15, 'merde': 5  # Can be funny in context
        }

    def score_segments(
        self,
        segments: List[Dict],
        num_clips: int = 3,
        target_duration: int = 45
    ) -> List[Dict[str, Any]]:
        """
        Score all segments and return top moments for clips

        Args:
            segments: Transcription segments with start, end, text
            num_clips: Number of clips to extract
            target_duration: Target duration per clip in seconds

        Returns:
            List of best clip suggestions with scores
        """
        try:
            logger.info(f"Scoring {len(segments)} segments for {num_clips} clips...")

            # Group segments into potential clips (target_duration windows)
            clip_candidates = self._create_clip_candidates(segments, target_duration)

            # Score each candidate
            scored_clips = []
            for candidate in clip_candidates:
                score = self._score_clip(candidate)

                # Add score to candidate
                candidate['score'] = score
                candidate['score_breakdown'] = score['breakdown']
                scored_clips.append(candidate)

            # Sort by total score
            scored_clips.sort(key=lambda x: x['score']['total'], reverse=True)

            # Take top N clips
            top_clips = scored_clips[:num_clips]

            # Format for output
            results = []
            for idx, clip in enumerate(top_clips):
                results.append({
                    'start_time': clip['start_time'],
                    'end_time': clip['end_time'],
                    'duration': clip['duration'],
                    'title': self._generate_title(clip),
                    'hook': self._generate_hook(clip),
                    'why_interesting': self._explain_score(clip),
                    'clip_text': clip['text'][:500],
                    'score': clip['score']['total'],
                    'start_segment_idx': clip['start_idx'],
                    'end_segment_idx': clip['end_idx']
                })

            logger.info(f"Found {len(results)} clips with scores: {[r['score'] for r in results]}")
            return results

        except Exception as e:
            logger.error(f"Error scoring segments: {e}", exc_info=True)
            return []

    def _create_clip_candidates(
        self,
        segments: List[Dict],
        target_duration: int
    ) -> List[Dict]:
        """Create sliding windows of segments as clip candidates"""
        candidates = []

        i = 0
        while i < len(segments):
            start_idx = i
            start_time = segments[i]['start']
            end_time = start_time
            clip_segments = []

            # Accumulate segments until we reach target duration
            j = i
            while j < len(segments) and (end_time - start_time) < target_duration * 1.5:
                clip_segments.append(segments[j])
                end_time = segments[j]['end']
                j += 1

            # Only consider clips between 20s and 90s
            duration = end_time - start_time
            if 20 <= duration <= 90:
                # Combine text
                text = ' '.join([s['text'] for s in clip_segments])

                candidates.append({
                    'start_idx': start_idx,
                    'end_idx': j - 1,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration,
                    'text': text,
                    'segments': clip_segments
                })

            # Move window by 25% of target duration
            i += max(1, len(clip_segments) // 4)

        return candidates

    def _score_clip(self, candidate: Dict) -> Dict[str, Any]:
        """Calculate comprehensive score for a clip candidate"""
        text = candidate['text'].lower()
        duration = candidate['duration']

        breakdown = {}
        total_score = 0

        # 1. Energy Keywords Score (max 50 points)
        energy_score = 0
        matched_keywords = []
        for keyword, weight in self.energy_keywords.items():
            count = text.count(keyword)
            if count > 0:
                energy_score += weight * min(count, 3)  # Cap at 3 occurrences
                matched_keywords.append(keyword)

        energy_score = min(energy_score, 50)
        breakdown['energy'] = energy_score
        total_score += energy_score

        # 2. Punctuation Energy Score (max 20 points)
        exclamations = text.count('!') + text.count('?')
        ellipsis = len(re.findall(r'\.{2,}', text))
        punct_score = min(exclamations * 5 + ellipsis * 3, 20)
        breakdown['punctuation'] = punct_score
        total_score += punct_score

        # 3. Question-Answer Pattern (max 25 points)
        qa_score = 0
        for qword in self.question_words:
            if qword in text:
                # Check if there's content after the question (potential answer/punchline)
                if len(text) > 50:
                    qa_score += 25
                    break
        breakdown['qa_pattern'] = qa_score
        total_score += qa_score

        # 4. Optimal Duration Score (max 15 points)
        target = 45
        duration_score = 15 - abs(duration - target) / 3
        duration_score = max(0, min(duration_score, 15))
        breakdown['duration'] = round(duration_score, 1)
        total_score += duration_score

        # 5. Text Density Score (max 15 points)
        # More words per second = more engaging
        word_count = len(text.split())
        words_per_second = word_count / max(duration, 1)
        density_score = min(words_per_second * 3, 15)
        breakdown['density'] = round(density_score, 1)
        total_score += density_score

        # 6. Repetition Bonus (catchphrases, emphasis) (max 10 points)
        words = text.split()
        word_freq = defaultdict(int)
        for word in words:
            if len(word) > 4:  # Ignore short words
                word_freq[word] += 1

        rep_score = 0
        for word, count in word_freq.items():
            if count >= 2:
                rep_score += 5
        rep_score = min(rep_score, 10)
        breakdown['repetition'] = rep_score
        total_score += rep_score

        # 7. Negative Words Penalty
        negative_score = 0
        for neg_word, penalty in self.negative_words.items():
            count = text.count(neg_word)
            negative_score += penalty * count

        breakdown['negativity'] = negative_score
        total_score += negative_score

        # 8. Capital Letters (shouting/emphasis) (max 10 points)
        original_text = candidate['text']
        caps_count = sum(1 for c in original_text if c.isupper())
        caps_ratio = caps_count / max(len(original_text), 1)
        caps_score = min(caps_ratio * 200, 10)
        breakdown['caps'] = round(caps_score, 1)
        total_score += caps_score

        return {
            'total': round(total_score, 1),
            'breakdown': breakdown,
            'matched_keywords': matched_keywords[:5]  # Top 5
        }

    def _generate_title(self, clip: Dict) -> str:
        """Generate catchy title from highest scoring keywords"""
        text = clip['text']
        score_info = clip['score']

        # Try to extract a catchy phrase
        sentences = re.split(r'[.!?]+', text)

        # Prefer short, punchy sentences
        for sentence in sentences:
            sentence = sentence.strip()
            if 5 <= len(sentence.split()) <= 12:
                # Capitalize first letter
                return sentence[0].upper() + sentence[1:50]

        # Fallback: use first sentence
        if sentences and sentences[0]:
            title = sentences[0].strip()[:50]
            return title[0].upper() + title[1:] if title else "Moment intéressant"

        return "Moment drôle"

    def _generate_hook(self, clip: Dict) -> str:
        """Generate hook phrase for first 3 seconds"""
        text = clip['text']

        # First sentence as hook
        first_sentence = re.split(r'[.!?]+', text)[0].strip()

        if len(first_sentence.split()) <= 10:
            return first_sentence

        # Take first 8 words
        words = text.split()[:8]
        return ' '.join(words) + '...'

    def _explain_score(self, clip: Dict) -> str:
        """Explain why this clip scored well"""
        breakdown = clip['score_breakdown']
        reasons = []

        if breakdown.get('energy', 0) > 20:
            reasons.append("Haute énergie et mots percutants")

        if breakdown.get('qa_pattern', 0) > 0:
            reasons.append("Format question-réponse engageant")

        if breakdown.get('punctuation', 0) > 10:
            reasons.append("Emphase et exclamations")

        if breakdown.get('density', 0) > 10:
            reasons.append("Rythme rapide et dynamique")

        if breakdown.get('repetition', 0) > 0:
            reasons.append("Phrases marquantes répétées")

        if not reasons:
            reasons.append("Moment engageant")

        return " • ".join(reasons)
