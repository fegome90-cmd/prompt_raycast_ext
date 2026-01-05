"""FormatConverter for LangChain to DSPy format conversion.

This module converts LangChain Hub prompt templates to the unified DSPy format
used by the few-shot pool. LangChain Hub stores prompts as templates (not input→output
pairs), so we extract components and generate synthetic inputs.
"""

import re
from typing import Dict


class FormatConverter:
    """Convert LangChain prompts to unified DSPy format.

    The unified DSPy format has the structure:
    {
        "inputs": {
            "original_idea": "<synthetic idea based on template>",
            "context": ""
        },
        "outputs": {
            "improved_prompt": "<template content>",
            "role": "<extracted role>",
            "directive": "<extracted directive>",
            "framework": "<detected framework>",
            "guardrails": "<extracted guardrails>"
        },
        "metadata": {
            "source": "langchain-hub",
            "source_handle": "<handle>",
            "source_name": "<name>"
        }
    }

    Example:
        >>> converter = FormatConverter()
        >>> lc_prompt = {
        ...     "handle": "hwchase17/react",
        ...     "name": "React",
        ...     "template": "You are a helpful assistant. Answer the following questions...",
        ...     "tags": ["agent", "react"]
        ... }
        >>> dspy_format = converter.to_dspy_format(lc_prompt)
        >>> print(dspy_format["outputs"]["role"])
        helpful assistant
    """

    # Regex patterns for extraction
    ROLE_PATTERNS = [
        r"You are (?:a|an) ([a-z][^.,!?\n]+)",  # "You are a/an..."
        r"Act as (?:a|an) ([a-z][^.,!?\n]+)",  # "Act as a/an..."
        r"Role:\s*([^\n]+)",  # "Role: ..." (with colon, more specific)
        r"Your role is (?:a|an) ([a-z][^.,!?\n]+)",  # "Your role is a/an..."
    ]

    DIRECTIVE_PATTERNS = [
        r"(?:Your )?(?:task|goal|objective|mission|directive)(?: is)?(?: to)?[:\s]+([^\n]+(?:\n[^A-Z].+)*?)(?=\n\n|\n[A-Z]|$)",
        r"([A-Z][^.!?]+[.!?])(?:\s+[A-Z])",  # First imperative sentence
    ]

    FRAMEWORK_KEYWORDS = {
        "ReAct": ["react", "observation", "action", "thought"],
        "Chain-of-Thought": ["reasoning", "thought", "step by step", "think", "reason"],
        "Decomposition": ["decompose", "break down", "step", "split", "divide"],
    }

    GUARDRAIL_PATTERNS = [
        r"(?:Do not|Don't|Never|Must not|Should not|Cannot|Avoid)(?:\s+[a-z]+)+[.!?]?",
        r"(?:NOT|RESTRICTED|FORBIDDEN|PROHIBITED)(?:\s+[A-Z]+)+",
        r"(?:constraint|limitation|restriction)(?:s)?[:\s]+([^\n]+(?:\n\s+[^A-Z\n].+)*?)(?=\n\n|\n[A-Z]|$)",
    ]

    def to_dspy_format(self, lc_prompt: Dict) -> Dict:
        """Convert LangChain prompt to unified DSPy format.

        Args:
            lc_prompt: LangChain prompt dict with keys:
                - handle: Prompt handle (e.g., "hwchase17/react")
                - name: Prompt name (e.g., "React")
                - template: Prompt template string
                - tags: Optional list of tags

        Returns:
            Dict in unified DSPy format with inputs, outputs, and metadata.

        Example:
            >>> lc_prompt = {
            ...     "handle": "hwchase17/react",
            ...     "name": "React",
            ...     "template": "You are a ReAct agent. Think step by step...",
            ...     "tags": ["agent"]
            ... }
            >>> result = converter.to_dspy_format(lc_prompt)
            >>> assert result["metadata"]["source"] == "langchain-hub"
            >>> assert "role" in result["outputs"]
        """
        template = lc_prompt.get("template", "")
        handle = lc_prompt.get("handle", "")
        name = lc_prompt.get("name", handle)
        tags = lc_prompt.get("tags", [])

        # Extract components from template
        role = self._extract_role(template)
        directive = self._extract_directive(template)
        framework = self._detect_framework(template, tags)
        guardrails = self._extract_guardrails(template)

        # Generate synthetic original_idea from template analysis
        original_idea = self._generate_synthetic_idea(
            template=template,
            role=role,
            framework=framework,
            handle=handle
        )

        # Build unified DSPy format
        return {
            "inputs": {
                "original_idea": original_idea,
                "context": ""
            },
            "outputs": {
                "improved_prompt": template,
                "role": role,
                "directive": directive,
                "framework": framework,
                "guardrails": guardrails
            },
            "metadata": {
                "source": "langchain-hub",
                "source_handle": handle,
                "source_name": name,
                "tags": tags
            }
        }

    def _extract_role(self, template: str) -> str:
        """Extract role from template.

        Looks for patterns like:
        - "You are a..."
        - "Act as a..."
        - "Role: ..."

        Args:
            template: Prompt template string

        Returns:
            Extracted role or "AI Assistant" if not found.

        Example:
            >>> converter = FormatConverter()
            >>> converter._extract_role("You are a helpful assistant...")
            'helpful assistant'
            >>> converter._extract_role("No role here")
            'AI Assistant'
        """
        template = template.strip()

        # Try each pattern
        for pattern in self.ROLE_PATTERNS:
            match = re.search(pattern, template, re.IGNORECASE)
            if match:
                role = match.group(1).strip()
                # Clean up common artifacts
                role = re.sub(r"\s+", " ", role)  # Normalize whitespace
                return role

        # Default fallback
        return "AI Assistant"

    def _extract_directive(self, template: str) -> str:
        """Extract main directive from template.

        Looks for imperative sentences, instructions, or task descriptions.
        Returns the first paragraph or key instruction section.

        Args:
            template: Prompt template string

        Returns:
            Extracted directive or empty string if not found.

        Example:
            >>> converter = FormatConverter()
            >>> converter._extract_directive("Your task is to help users. Answer questions...")
            'help users'
        """
        template = template.strip()

        # Try to find explicit task/goal/objective statements
        for pattern in self.DIRECTIVE_PATTERNS:
            match = re.search(pattern, template, re.IGNORECASE | re.MULTILINE)
            if match:
                directive = match.group(1).strip()
                # Clean up: remove extra whitespace, limit length
                directive = re.sub(r"\s+", " ", directive)
                if len(directive) > 200:
                    directive = directive[:197] + "..."
                return directive

        # Fallback: extract first paragraph (first block of text)
        paragraphs = template.split("\n\n")
        if paragraphs:
            first_para = paragraphs[0].strip()
            # Remove role statements
            first_para = re.sub(r"You are an? [^.]+\.?\s*", "", first_para, flags=re.IGNORECASE)
            first_para = first_para.strip()

            if first_para and len(first_para) > 10:
                # Limit length
                if len(first_para) > 200:
                    first_para = first_para[:197] + "..."
                return first_para

        return ""

    def _detect_framework(self, template: str, tags: list = None) -> str:
        """Detect framework from template content and tags.

        Frameworks detected:
        - "Chain-of-Thought": If "react", "thought", "reasoning" in template/tags
        - "Decomposition": If "decompose", "step", "break down" in template
        - "ReAct": If "react", "observation", "action" in template
        - "": Empty string if no framework detected

        Args:
            template: Prompt template string
            tags: Optional list of tags from LangChain Hub

        Returns:
            Detected framework name or empty string.

        Example:
            >>> converter = FormatConverter()
            >>> converter._detect_framework("Use ReAct to think step by step")
            'ReAct'
            >>> converter._detect_framework("Just answer questions")
            ''
        """
        template_lower = template.lower()
        tags = tags or []
        tags_lower = [tag.lower() for tag in tags]

        # Check each framework
        for framework_name, keywords in self.FRAMEWORK_KEYWORDS.items():
            # Check in template
            for keyword in keywords:
                if keyword in template_lower:
                    return framework_name

            # Check in tags
            for keyword in keywords:
                if keyword in tags_lower:
                    return framework_name

        return ""

    def _extract_guardrails(self, template: str) -> str:
        """Extract guardrails/constraints from template.

        Looks for negative constraints and limitations:
        - "Do not...", "Don't...", "Never..."
        - "Must not...", "Should not..."
        - Constraint sections

        Args:
            template: Prompt template string

        Returns:
            Comma-separated guardrails or empty string if none found.

        Example:
            >>> converter = FormatConverter()
            >>> converter._extract_guardrails("Don't share personal info. Never lie.")
            'Don't share personal info., Never lie.'
        """
        template = template.strip()
        guardrails = []

        # Try each pattern
        for pattern in self.GUARDRAIL_PATTERNS:
            matches = re.finditer(pattern, template, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                guardrail = match.group(0).strip()
                # Clean up whitespace
                guardrail = re.sub(r"\s+", " ", guardrail)
                if guardrail:
                    guardrails.append(guardrail)

        # Return as comma-separated string or empty string
        return ", ".join(guardrails) if guardrails else ""

    def _generate_synthetic_idea(
        self,
        template: str,
        role: str,
        framework: str,
        handle: str
    ) -> str:
        """Generate synthetic original_idea from template analysis.

        Creates a realistic input that would produce this template.
        Uses handle, role, and framework to generate contextually appropriate input.

        Args:
            template: Original template content
            role: Extracted role
            framework: Detected framework
            handle: Prompt handle from LangChain Hub

        Returns:
            Synthetic input string.

        Example:
            >>> converter = FormatConverter()
            >>> idea = converter._generate_synthetic_idea(
            ...     "You are a ReAct agent...",
            ...     "ReAct agent",
            ...     "ReAct",
            ...     "hwchase17/react"
            ... )
            >>> assert "ReAct" in idea
        """
        # Use handle as hint for intent
        handle_parts = handle.split("/")[-1].split("-")
        handle_hint = handle_parts[0] if handle_parts else ""

        # Build synthetic idea from components
        parts = []

        # Add framework context if available
        if framework:
            parts.append(f"Create {framework.lower()} agent prompt")

        # Add role context
        if role and role != "AI Assistant":
            parts.append(f"for {role}")

        # Add handle hint if meaningful
        if handle_hint and handle_hint.lower() not in str(role).lower():
            parts.append(f"using {handle_hint} pattern")

        # Fallback if no parts
        if not parts:
            # Generate from template keywords
            template_lower = template.lower()
            if "agent" in template_lower:
                return "Create AI agent prompt"
            elif "assistant" in template_lower:
                return "Create assistant prompt"
            else:
                return f"Create prompt based on {handle}"

        synthetic_idea = " ".join(parts)

        # Ensure it ends like a natural request
        if not synthetic_idea.endswith("."):
            synthetic_idea += " prompt" if not synthetic_idea.endswith("prompt") else ""

        return synthetic_idea
