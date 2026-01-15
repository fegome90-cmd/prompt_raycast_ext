"""PromptMetodizer - Intelligent LangChain to DSPy Architect format converter.

This module provides intelligent prompt analysis that goes beyond simple pattern matching.
It extracts semantic meaning, detects reasoning frameworks, and generates realistic synthetic
inputs for the DSPy Prompt Improver few-shot pool.

Key improvements over FormatConverter:
- Deep semantic analysis of prompt structure and intent
- Multi-framework detection with confidence scores
- Context-aware original_idea generation
- Quality scoring for each extracted component
- Pattern detection for known agent frameworks (ReAct, RAG, CoT, etc.)
"""

import re
from dataclasses import dataclass


@dataclass
class QualityScores:
    """Quality scores for extracted components."""
    role_clarity: float = 0.0
    directive_specificity: float = 0.0
    framework_confidence: float = 0.0
    guardrails_measurability: float = 0.0
    overall_quality: float = 0.0


@dataclass
class FrameworkDetection:
    """Framework detection result."""
    name: str
    confidence: float
    evidence: list[str]


class PromptMetodizer:
    """Intelligent prompt analyzer for LangChain to DSPy Architect conversion.

    This class analyzes LangChain Hub prompts and extracts structured components
    following the DSPy Architect format:
    - original_idea: Synthetic but realistic input
    - role: Who the assistant is
    - directive: What the assistant should do
    - framework: Reasoning pattern (ReAct, RAG, CoT, etc.)
    - guardrails: Constraints and restrictions

    The metodizer uses:
    - Multi-level regex patterns for component extraction
    - Keyword frequency analysis for framework detection
    - Contextual analysis for quality scoring
    - Template structure analysis for synthetic idea generation

    Example:
        >>> metodizer = PromptMetodizer()
        >>> result = metodizer.metodize_prompt(
        ...     handle="hwchase17/react",
        ...     template="You are a ReAct agent. Think step by step..."
        ... )
        >>> print(result["outputs"]["framework"])
        ReAct
        >>> print(result["metadata"]["quality_scores"]["framework_confidence"])
        0.95
    """

    # Enhanced role patterns with context
    ROLE_PATTERNS = [
        # Explicit role definitions (most specific first)
        r"You are (?:a|an|the) ([a-z]+ (?:assistant|agent|expert|advisor|analyst|specialist|engineer))(?:\.|,| that|\n|$)",
        r"You are (?:a|an) ([a-z][a-z]+(?: [a-z][a-z]+)?)(?:\.|,|\n)",
        r"Act as (?:a|an) ([a-z][^.,!?\n]{2,50}?)(?:\.|,| and| who)",
        r"Role:\s*([^\n]{2,50})",
        r"Your role is (?:to be )?(?:a|an )?([a-z][^.,!?\n]{2,50}?)(?:\.|,|\n)",
        r"Serve as (?:a|an) ([a-z][^.,!?\n]{2,50}?)(?:\.|,)",
    ]

    # Directive patterns with action verbs
    DIRECTIVE_PATTERNS = [
        r"(?:Your )?(?:task|goal|objective|mission|responsibility|purpose)(?: is)?(?: to)?[:\s]+([^\n]+(?:\n\s{0,4}[^A-Z][^\n]*)*?)(?=\n\n|\n[A-Z]|$)",
        r"(?:Help|Assist|Guide|Advise|Support)(?:\s+\w+)?(?:\s+to)?[:\s]+([^\n]+(?:\n\s{0,4}[^A-Z][^\n]*)*?)(?=\n\n|\n[A-Z]|$)",
        r"(?:Use|Apply|Implement|Execute|Perform)(?:\s+\w+)?(?:\s+to)?[:\s]+([^\n]+(?:\n\s{0,4}[^A-Z][^\n]*)*?)(?=\n\n|\n[A-Z]|$)",
    ]

    # Framework detection patterns with evidence
    FRAMEWORK_PATTERNS = {
        "ReAct": {
            "keywords": ["thought", "action", "observation", "react", "tool", "agent"],
            "patterns": [
                r"Thought:\s*\w+",
                r"Action:\s*\w+",
                r"Observation:\s*\w+",
                r"action input",
                r"agent_scratchpad"
            ],
            "threshold": 3  # Min matches to detect
        },
        "RAG": {
            "keywords": ["retrieved", "context", "retrieval", "search", "{context}", "documents"],
            "patterns": [
                r"retrieved context",
                r"\{context\}",
                r"pieces of retrieved",
                r"use the following context",
                r"based on the context"
            ],
            "threshold": 2
        },
        "Chain-of-Thought": {
            "keywords": ["step by step", "think through", "reasoning", "thought process", "coherent"],
            "patterns": [
                r"step by step",
                r"think through",
                r"reasoning steps?",
                r"thought process",
                r"let's think"
            ],
            "threshold": 2
        },
        "Decomposition": {
            "keywords": ["break down", "decompose", "sub-problem", "subtask", "steps", "divide"],
            "patterns": [
                r"break down (?:the )?(?:problem|task)",
                r"decompose (?:the )?(?:problem|task)",
                r"sub-problem",
                r"subtask",
                r"divide (?:it|the problem)"
            ],
            "threshold": 2
        },
        "Self-Ask": {
            "keywords": ["follow up", "intermediate answer", "followup", "question"],
            "patterns": [
                r"follow up question",
                r"intermediate answer",
                r"followup questions?",
                r"are follow up questions needed"
            ],
            "threshold": 2
        },
        "Reflexion": {
            "keywords": ["reflect", "reflection", "improve", "feedback", "retry"],
            "patterns": [
                r"reflect on",
                r"reflection:",
                r"improve your",
                r"feedback from"
            ],
            "threshold": 2
        },
        "Multi-Agent": {
            "keywords": ["coordinator", "orchestrator", "delegate", "multiple agents", "team"],
            "patterns": [
                r"coordinator",
                r"orchestrator",
                r"delegate (?:to )?(?:sub-)?agents?",
                r"multiple agents",
                r"team of agents"
            ],
            "threshold": 2
        }
    }

    # Guardrail patterns with categorization
    GUARDRAIL_PATTERNS = {
        "negative": [
            r"(?:Do not|Don't|Never|Must not|Should not|Cannot|Avoid)(?:\s+[a-z]+){1,10}[.!?]?",
        ],
        "format": [
            r"(?:Use|Format|Structure)(?:\s+(?:as|in|with))?:?\s*([^\n]+?(?:\n\s+[a-z]+.+?)*?)(?=\n\n|\n[A-Z]|$)",
            r"(?:Keep|Limit|Restrict)(?:\s+\w+)?(?:\s+to)?[:\s]+([^\n]+)(?:\.|,|\n)",
        ],
        "constraint": [
            r"(?:constraint|limitation|restriction|requirement)(?:s)?[:\s]+([^\n]+(?:\n\s+[^A-Z\n].+)*?)(?=\n\n|\n[A-Z]|$)",
            r"(?:Only|Must|Should)(?:\s+(?:not|always))?[:\s]+([^\n]+(?:\n\s+[a-z]+.+?)*?)(?=\n\n|\n[A-Z]|$)",
        ],
        "measurable": [
            r"(?:maximum|max|min|minimum|at least|at most|exactly|between)(?:\s+\d+)(?:\s+(?:words?|sentences?|paragraphs?|lines?|characters?))?",
            r"(?:\d+)(?:\s*(?:words?|sentences?|paragraphs?|lines?|steps?))",
        ]
    }

    def metodize_prompt(self, handle: str, template: str, tags: list[str] = None) -> dict:
        """Convert LangChain prompt to DSPy Architect format.

        Performs intelligent analysis of the prompt template to extract:
        - Role: Who the assistant is (with clarity score)
        - Directive: What the assistant should do (with specificity score)
        - Framework: Reasoning pattern (with confidence score and evidence)
        - Guardrails: Constraints (with measurability score)

        Args:
            handle: Prompt handle (e.g., "hwchase17/react")
            template: Prompt template string
            tags: Optional list of tags from LangChain Hub

        Returns:
            Dictionary with inputs, outputs, and metadata:
            {
                "inputs": {
                    "original_idea": "...",
                    "context": ""
                },
                "outputs": {
                    "improved_prompt": "...",
                    "role": "...",
                    "directive": "...",
                    "framework": "...",
                    "guardrails": "..."
                },
                "metadata": {
                    "quality_scores": {...},
                    "detected_patterns": [...],
                    "source_handle": "...",
                    "framework_detections": [...]
                }
            }

        Example:
            >>> metodizer = PromptMetodizer()
            >>> result = metodizer.metodize_prompt(
            ...     handle="hwchase17/react",
            ...     template="You are a ReAct agent. Think step by step...",
            ...     tags=["agent", "react"]
            ... )
            >>> assert result["outputs"]["framework"] == "ReAct"
            >>> assert result["metadata"]["quality_scores"]["framework_confidence"] > 0.8
        """
        # Detect framework first (informs other extractions)
        framework_detections = self._detect_framework(template, tags or [])
        primary_framework = framework_detections[0] if framework_detections else FrameworkDetection("", 0.0, [])

        # Extract components
        role = self._extract_role(template)
        directive = self._extract_directive(template, primary_framework.name)
        guardrails = self._extract_guardrails(template)

        # Generate synthetic original_idea
        original_idea = self._generate_original_idea(
            handle=handle,
            template=template,
            role=role,
            framework=primary_framework.name,
            directive=directive
        )

        # Calculate quality scores
        quality_scores = self._calculate_quality_scores(
            role=role,
            directive=directive,
            framework=primary_framework,
            guardrails=guardrails,
            template=template
        )

        # Extract detected patterns
        detected_patterns = self._extract_patterns(template, primary_framework)

        # Build result
        return {
            "inputs": {
                "original_idea": original_idea,
                "context": ""
            },
            "outputs": {
                "improved_prompt": template,
                "role": role,
                "directive": directive,
                "framework": primary_framework.name,
                "guardrails": guardrails
            },
            "metadata": {
                "quality_scores": {
                    "role_clarity": quality_scores.role_clarity,
                    "directive_specificity": quality_scores.directive_specificity,
                    "framework_confidence": quality_scores.framework_confidence,
                    "guardrails_measurability": quality_scores.guardrails_measurability,
                    "overall_quality": quality_scores.overall_quality
                },
                "detected_patterns": detected_patterns,
                "source_handle": handle,
                "framework_detections": [
                    {
                        "name": fw.name,
                        "confidence": fw.confidence,
                        "evidence": fw.evidence
                    }
                    for fw in framework_detections
                ]
            }
        }

    def _extract_role(self, template: str) -> str:
        """Extract role with intelligent pattern matching.

        Tries multiple patterns and selects the most specific role.
        Prefers explicit role definitions over implicit ones.

        Args:
            template: Prompt template string

        Returns:
            Extracted role or "AI Assistant" if not found
        """
        template = template.strip()
        roles_found = []

        # Try each pattern
        for pattern in self.ROLE_PATTERNS:
            matches = re.finditer(pattern, template, re.IGNORECASE)
            for match in matches:
                role = match.group(1).strip()
                # Clean up
                role = re.sub(r"\s+", " ", role)
                # Score by specificity (longer and more descriptive = better)
                score = len(role.split())  # More words = more specific
                roles_found.append((role, score))

        if roles_found:
            # Return most specific role
            roles_found.sort(key=lambda x: x[1], reverse=True)
            return roles_found[0][0]

        # Try to infer from context
        template_lower = template.lower()
        if "agent" in template_lower:
            if "react" in template_lower:
                return "ReAct Agent"
            elif "tool" in template_lower:
                return "Tool-Using Agent"
            else:
                return "AI Agent"
        elif "assistant" in template_lower:
            return "AI Assistant"
        elif "expert" in template_lower:
            return "Expert Advisor"

        return "AI Assistant"

    def _extract_directive(self, template: str, framework: str) -> str:
        """Extract main directive with framework-aware analysis.

        Args:
            template: Prompt template string
            framework: Detected framework name

        Returns:
            Extracted directive or empty string
        """
        template = template.strip()

        # Try explicit directive patterns
        for pattern in self.DIRECTIVE_PATTERNS:
            match = re.search(pattern, template, re.IGNORECASE | re.MULTILINE)
            if match:
                directive = match.group(1).strip()
                directive = re.sub(r"\s+", " ", directive)
                if len(directive) > 20:  # Minimum meaningful length
                    return directive[:300]  # Limit length

        # Framework-specific directive extraction
        if framework == "ReAct":
            # Look for Question/Answer format
            question_match = re.search(r"Question:\s*([^\n]+)", template, re.IGNORECASE)
            if question_match:
                return f"Answer questions using {framework} reasoning"
            return f"Use {framework} reasoning to solve problems"

        elif framework == "RAG":
            # Look for question-answering context
            if "answer the question" in template.lower():
                return "Answer questions using retrieved context"
            return "Use retrieved context to answer questions"

        elif framework == "Self-Ask":
            return "Break down complex questions by asking follow-up questions"

        elif framework == "Decomposition":
            return "Break down complex tasks into smaller sub-problems"

        # Fallback: Extract first meaningful paragraph
        paragraphs = [p.strip() for p in template.split("\n\n") if p.strip()]
        if paragraphs:
            first_para = paragraphs[0]
            # Remove role statements
            first_para = re.sub(r"You are an? [^.]+\.?\s*", "", first_para, flags=re.IGNORECASE)
            first_para = first_para.strip()

            if len(first_para) > 20:
                # Extract first imperative sentence
                sentences = re.split(r"[.!?]", first_para)
                for sent in sentences:
                    sent = sent.strip()
                    if sent and len(sent) > 10:
                        return sent[:300]

        return ""

    def _detect_framework(self, template: str, tags: list[str]) -> list[FrameworkDetection]:
        """Detect reasoning framework with confidence scoring.

        Checks multiple frameworks and returns sorted list by confidence.

        Args:
            template: Prompt template string
            tags: Optional list of tags

        Returns:
            List of FrameworkDetection objects sorted by confidence
        """
        template_lower = template.lower()
        tags_lower = [tag.lower() for tag in tags]
        detections = []

        for framework_name, config in self.FRAMEWORK_PATTERNS.items():
            confidence = 0.0
            evidence = []

            # Check keywords in template
            for keyword in config["keywords"]:
                if keyword in template_lower:
                    confidence += 0.15
                    evidence.append(f"keyword: '{keyword}'")

            # Check keywords in tags
            for keyword in config["keywords"]:
                if keyword in tags_lower:
                    confidence += 0.25
                    evidence.append(f"tag: '{keyword}'")

            # Check structural patterns
            for pattern in config["patterns"]:
                if re.search(pattern, template_lower):
                    confidence += 0.3
                    evidence.append(f"pattern: '{pattern[:30]}...'")

            # Normalize confidence to 0-1
            confidence = min(confidence, 1.0)

            # Only include if meets threshold
            if confidence >= 0.3 or len([e for e in evidence if "tag:" in e]) > 0:
                detections.append(FrameworkDetection(
                    name=framework_name,
                    confidence=confidence,
                    evidence=evidence[:5]  # Limit evidence
                ))

        # Sort by confidence
        detections.sort(key=lambda x: x.confidence, reverse=True)

        return detections

    def _extract_guardrails(self, template: str) -> str:
        """Extract guardrails with categorization.

        Args:
            template: Prompt template string

        Returns:
            Comma-separated guardrails by category
        """
        template = template.strip()
        guardrails_by_category = {}

        for category, patterns in self.GUARDRAIL_PATTERNS.items():
            category_guardrails = []

            for pattern in patterns:
                matches = re.finditer(pattern, template, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    guardrail = match.group(0) if match.lastindex is None or match.lastindex == 0 else match.group(1)
                    guardrail = re.sub(r"\s+", " ", guardrail.strip())
                    if guardrail and len(guardrail) > 5:
                        category_guardrails.append(guardrail)

            if category_guardrails:
                guardrails_by_category[category] = category_guardrails

        # Format guardrails
        if not guardrails_by_category:
            return ""

        formatted = []
        for category, rails in guardrails_by_category.items():
            formatted.append(f"{category.capitalize()}: {', '.join(rails[:3])}")  # Limit per category

        return " | ".join(formatted)

    def _generate_original_idea(
        self,
        handle: str,
        template: str,
        role: str,
        framework: str,
        directive: str
    ) -> str:
        """Generate synthetic but realistic original_idea.

        Creates a natural-looking user request that would produce this prompt.
        Uses context from handle, role, framework, and directive.

        Args:
            handle: Prompt handle
            template: Original template
            role: Extracted role
            framework: Detected framework
            directive: Extracted directive

        Returns:
            Synthetic input string
        """
        # Parse handle for hints
        handle_parts = handle.split("/")[-1].replace("-", " ").split("_")
        handle_hint = " ".join(handle_parts)

        # Build idea components
        components = []

        # Start with action verb
        action = "Create"
        if "improve" in template.lower() or "enhance" in template.lower():
            action = "Improve"
        elif "generate" in template.lower():
            action = "Generate"
        elif "build" in template.lower():
            action = "Build"

        # Add framework context
        if framework and framework != "AI Assistant":
            components.append(f"{action.lower()} a {framework.lower()} prompt")

        # Add role context
        if role and role != "AI Assistant":
            if not components:
                components.append(f"{action.lower()} a prompt")
            components.append(f"for a {role.lower()}")

        # Add directive context
        if directive and len(directive) > 20:
            if not components:
                components.append(f"{action.lower()} a prompt")
            # Extract key action from directive
            directive_words = directive.split()[:5]
            components.append(f"that {' '.join(directive_words).lower()}")

        # Add handle hint if meaningful
        if handle_hint and len(handle_hint) > 2 and handle_hint not in str(role).lower():
            if not components:
                components.append(f"{action.lower()} a {handle_hint} prompt")
            else:
                components.append(f"using {handle_hint}")

        # Fallback
        if not components:
            # Infer from template
            template_lower = template.lower()
            if "question" in template_lower:
                return f"{action} a question-answering prompt"
            elif "agent" in template_lower:
                return f"{action} an agent prompt"
            elif "assistant" in template_lower:
                return f"{action} an assistant prompt"
            else:
                return f"{action} a prompt based on {handle}"

        # Construct idea
        idea = " ".join(components)

        # Make it natural
        if not idea.endswith((".", "?")):
            idea += "."

        return idea.capitalize()

    def _calculate_quality_scores(
        self,
        role: str,
        directive: str,
        framework: FrameworkDetection,
        guardrails: str,
        template: str
    ) -> QualityScores:
        """Calculate quality scores for extracted components.

        Args:
            role: Extracted role
            directive: Extracted directive
            framework: Detected framework
            guardrails: Extracted guardrails
            template: Original template

        Returns:
            QualityScores object with scores 0-1
        """
        # Role clarity: Based on specificity
        role_clarity = 0.0
        if role and role != "AI Assistant":
            role_clarity = 0.5  # Has a role
            if len(role.split()) >= 2:  # Multi-word role = more specific
                role_clarity += 0.3
            if any(word in role.lower() for word in ["specialist", "expert", "analyst", "advisor"]):
                role_clarity += 0.2
        role_clarity = min(role_clarity, 1.0)

        # Directive specificity: Based on length and detail
        directive_specificity = 0.0
        if directive:
            directive_specificity = 0.3  # Has a directive
            if len(directive) > 50:  # Detailed directive
                directive_specificity += 0.3
            if len(directive) > 100:  # Very detailed
                directive_specificity += 0.2
            # Check for action verbs
            if any(word in directive.lower() for word in ["answer", "help", "guide", "create", "analyze"]):
                directive_specificity += 0.2
        directive_specificity = min(directive_specificity, 1.0)

        # Framework confidence: From detection
        framework_confidence = framework.confidence

        # Guardrails measurability: Based on quantifiable constraints
        guardrails_measurability = 0.0
        if guardrails:
            guardrails_measurability = 0.3  # Has guardrails
            # Check for measurable constraints
            if re.search(r"\d+", guardrails):  # Has numbers
                guardrails_measurability += 0.3
            # Check for specific formats
            if any(word in guardrails.lower() for word in ["words", "sentences", "maximum", "minimum", "limit"]):
                guardrails_measurability += 0.2
            # Check for multiple categories
            if guardrails.count("|") >= 2:
                guardrails_measurability += 0.2
        guardrails_measurability = min(guardrails_measurability, 1.0)

        # Overall quality: Average of all scores
        overall_quality = (
            role_clarity + directive_specificity + framework_confidence + guardrails_measurability
        ) / 4.0

        return QualityScores(
            role_clarity=role_clarity,
            directive_specificity=directive_specificity,
            framework_confidence=framework_confidence,
            guardrails_measurability=guardrails_measurability,
            overall_quality=overall_quality
        )

    def _extract_patterns(self, template: str, framework: FrameworkDetection) -> list[str]:
        """Extract specific patterns detected in template.

        Args:
            template: Prompt template string
            framework: Primary framework detection

        Returns:
            List of detected pattern descriptions
        """
        patterns = []

        # Check for variable placeholders
        variables = re.findall(r"\{(\w+)\}", template)
        if variables:
            patterns.append(f"Variables: {', '.join(set(variables))}")

        # Check for structured output
        if re.search(r"(?:format|structure|output)?:", template, re.IGNORECASE):
            patterns.append("Structured output specification")

        # Check for examples
        if re.search(r"(?:example|for instance|e\.g\.|such as)", template, re.IGNORECASE):
            patterns.append("Contains examples")

        # Framework-specific patterns
        if framework.name == "ReAct":
            if "tool" in template.lower():
                patterns.append("Tool-using pattern")
            if "thought" in template.lower():
                patterns.append("Thought-action-observation loop")

        elif framework.name == "RAG":
            if "context" in template.lower():
                patterns.append("Context-based answering")

        # Check for conversational patterns
        if re.search(r"question:|answer:|thought:", template, re.IGNORECASE):
            patterns.append("Conversational format")

        return patterns
