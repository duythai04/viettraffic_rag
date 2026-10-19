import re
from collections import Counter


class LegalParser:

    ARTICLE_PATTERN = re.compile(
        r"(?mi)^[ \t]*"
        r"[._\-|]*"
        r"[ \t]*"
        r"(?:Điều|Diều|Điêu)"
        r"[ \t]+"
        r"(\d+[a-zA-Z]?)"
        r"[ \t]*\."
        r"[ \t]*(.*)$"
    )

    CLAUSE_PATTERN = re.compile(
        r"(?m)^[ \t]*"
        r"[._\-|:]*"
        r"[ \t]*"
        r"(\d+)"
        r"[ \t]*"
        r"(?:\.{1,2}|::)"
        r"(?![ \t]*\d{3}\b)"
        r"[ \t]*"
        r"(.+)$"
    )

    POINT_PATTERN = re.compile(
        r"(?mi)^[ \t]*"
        r"[._\-|:]*"
        r"[ \t]*"
        r"([a-zđ])"
        r"[ \t]*\)"
        r"[ \t]+"
        r"(.+)$"
    )

    OCR_NOISE_PATTERN = re.compile(
        r"^[\s\-_.*|;:'\"<>°`]+$"
    )

    POINT_ORDER = [
        "a",
        "b",
        "c",
        "d",
        "đ",
        "e",
        "g",
        "h",
        "i",
        "k",
        "l",
        "m",
        "n",
        "o",
        "p",
        "q",
        "r",
        "s",
        "t",
        "u",
        "v",
        "x",
        "y",
    ]

    def parse_articles(
        self,
        text: str,
    ) -> list[dict]:

        if not text:
            return []

        matches = list(
            self.ARTICLE_PATTERN.finditer(text)
        )

        articles = []

        for index, match in enumerate(matches):
            article_number = match.group(1).strip()
            first_title_line = match.group(2).strip()

            body_start = match.end()

            body_end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(text)
            )

            article_body = text[
                body_start:body_end
            ].strip()

            article_title, content = (
                self._extract_title_and_content(
                    first_title_line,
                    article_body,
                )
            )

            clauses = self.parse_clauses(
                content
            )

            articles.append(
                {
                    "article_number": article_number,
                    "article_title": article_title,
                    "content": content,
                    "clauses": clauses,
                }
            )

        return articles

    def _extract_title_and_content(
        self,
        first_title_line: str,
        article_body: str,
    ) -> tuple[str, str]:

        lines = article_body.splitlines()
        title_parts = []

        if first_title_line:
            title_parts.append(
                first_title_line
            )

        content_start_index = None

        for index, line in enumerate(lines):
            stripped = line.strip()

            if not stripped:
                continue

            if self._is_noise_line(stripped):
                continue

            normalized_line = (
                self._normalize_clause_ocr(
                    stripped
                )
            )

            if self.CLAUSE_PATTERN.match(
                normalized_line
            ):
                content_start_index = index
                break

            title_parts.append(stripped)

        if content_start_index is not None:
            content = "\n".join(
                lines[content_start_index:]
            ).strip()

        else:
            title_parts = []

            if first_title_line:
                title_parts.append(
                    first_title_line
                )

            content = article_body.strip()

        article_title = self._join_title_lines(
            title_parts
        )

        return article_title, content

    def _normalize_clause_ocr(
        self,
        text: str,
    ) -> str:

        if not text:
            return ""

        text = re.sub(
            r"(?mi)^"
            r"([ \t]*[._\-|:]*[ \t]*)"
            r"(\d+)"
            r"[ \t]*,[ \t]*"
            r"(Phạt|Phat)\b",
            r"\1\2. \3",
            text,
        )

        return text

    def parse_clauses(
        self,
        article_content: str,
    ) -> list[dict]:

        if not article_content:
            return []

        normalized_content = (
            self._normalize_clause_ocr(
                article_content
            )
        )

        matches = list(
            self.CLAUSE_PATTERN.finditer(
                normalized_content
            )
        )

        clauses = []

        for index, match in enumerate(matches):
            clause_number = (
                match.group(1).strip()
            )

            first_line = (
                match.group(2).strip()
            )

            content_start = match.end()

            content_end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(normalized_content)
            )

            remaining_content = (
                normalized_content[
                    content_start:content_end
                ].strip()
            )

            if remaining_content:
                full_content = (
                    first_line
                    + "\n"
                    + remaining_content
                )
            else:
                full_content = first_line

            full_content = full_content.strip()

            points = self.parse_points(
                full_content
            )

            clauses.append(
                {
                    "clause_number": clause_number,
                    "content": full_content,
                    "points": points,
                }
            )

        return clauses

    def _normalize_point_ocr(
        self,
        text: str,
    ) -> str:

        if not text:
            return ""

        lines = text.splitlines()

        self._normalize_simple_point_ocr(
            lines
        )

        self._normalize_contextual_points(
            lines
        )

        self._normalize_d_dstroke_points(
            lines
        )

        return "\n".join(lines)

    def _normalize_simple_point_ocr(
        self,
        lines: list[str],
    ) -> None:

        for index, line in enumerate(lines):

            line = re.sub(
                r"^([ \t]*[._\-|:]*[ \t]*)"
                r"[“”\"']+"
                r"([a-zđ])"
                r"[ \t]*\)",
                r"\1\2)",
                line,
                count=1,
                flags=re.IGNORECASE,
            )

            line = re.sub(
                r"^([ \t]*[._\-|:]*[ \t]*)"
                r"i[ \t]*\}",
                r"\1i)",
                line,
                count=1,
                flags=re.IGNORECASE,
            )

            line = re.sub(
                r"^([ \t]*[._\-|:]*[ \t]*)"
                r"ø[ \t]*\)",
                r"\1g)",
                line,
                count=1,
                flags=re.IGNORECASE,
            )

            lines[index] = line

    def _normalize_contextual_points(
        self,
        lines: list[str],
    ) -> None:

        max_passes = 4

        for _ in range(max_passes):
            changed = False

            for index, line in enumerate(lines):

                if self._extract_point_marker(line):
                    continue

                previous = self._find_previous_point(
                    lines,
                    index,
                )

                following = self._find_next_point(
                    lines,
                    index,
                )

                expected = (
                    self._expected_between(
                        previous,
                        following,
                    )
                )

                if expected is None:
                    continue

                candidate = (
                    self._extract_ocr_point_candidate(
                        line
                    )
                )

                if candidate is None:
                    continue

                if expected not in candidate:
                    continue

                replacement = (
                    self._replace_ocr_candidate(
                        line,
                        expected,
                    )
                )

                if replacement != line:
                    lines[index] = replacement
                    changed = True

            if not changed:
                break

        self._normalize_terminal_candidates(
            lines
        )

    def _expected_between(
        self,
        previous: str | None,
        following: str | None,
    ) -> str | None:

        if (
            previous not in self.POINT_ORDER
            or following not in self.POINT_ORDER
        ):
            return None

        previous_index = (
            self.POINT_ORDER.index(
                previous
            )
        )

        following_index = (
            self.POINT_ORDER.index(
                following
            )
        )

        if following_index - previous_index != 2:
            return None

        return self.POINT_ORDER[
            previous_index + 1
        ]

    def _extract_ocr_point_candidate(
        self,
        line: str,
    ) -> set[str] | None:

        stripped = line.strip()

        if not stripped:
            return None

        candidates = set()

        if re.match(
            r"^[._\-|:\s]*1\s*\)",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.update(
                {"i", "l"}
            )

        if re.match(
            r"^[._\-|:\s]*0\s*\)",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.add("o")

        if re.match(
            r"^[._\-|:\s]*9\s*\)",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.add("d")

        if re.match(
            r"^[._\-|:\s]*8\s*\)",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.add("g")

        if re.match(
            r"^[._\-|:\s]*[©¢]\s*\)",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.add("c")

        if re.match(
            r"^[._\-|:\s]*£\s*\)",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.add("e")

        if re.match(
            r"^[._\-|:\s]*ø\s*\)",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.add("g")

        if re.match(
            r"^[._\-|:\s]*là\s*\)",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.add("c")

        if re.match(
            r"^[._\-|:\s]*kỳ\b",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.add("k")

        if re.match(
            r"^[._\-|:\s]*"
            r"_*\]*\s*\)"
            r"\s+",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.add("i")

        if re.match(
            r"^[._\-|:\s]*4\s+",
            stripped,
            flags=re.IGNORECASE,
        ):
            candidates.add("d")

        if not candidates:
            return None

        return candidates

    def _replace_ocr_candidate(
        self,
        line: str,
        marker: str,
    ) -> str:

        prefix_match = re.match(
            r"^([ \t]*[._\-|:]*[ \t]*)",
            line,
        )

        prefix = (
            prefix_match.group(1)
            if prefix_match
            else ""
        )

        stripped = line[
            len(prefix):
        ]

        patterns = [
            r"^1\s*\)\s*",
            r"^0\s*\)\s*",
            r"^9\s*\)\s*",
            r"^8\s*\)\s*",
            r"^[©¢]\s*\)\s*",
            r"^£\s*\)\s*",
            r"^ø\s*\)\s*",
            r"^là\s*\)\s*",
            r"^kỳ\s*",
            r"^_*\]*\s*\)\s*",
            r"^4\s+",
        ]

        for pattern in patterns:
            if re.match(
                pattern,
                stripped,
                flags=re.IGNORECASE,
            ):
                content = re.sub(
                    pattern,
                    "",
                    stripped,
                    count=1,
                    flags=re.IGNORECASE,
                )

                return (
                    f"{prefix}"
                    f"{marker}) "
                    f"{content.lstrip()}"
                )

        return line

    def _normalize_terminal_candidates(
        self,
        lines: list[str],
    ) -> None:

        for index, line in enumerate(lines):

            if self._extract_point_marker(line):
                continue

            candidate = (
                self._extract_ocr_point_candidate(
                    line
                )
            )

            if candidate is None:
                continue

            previous = self._find_previous_point(
                lines,
                index,
            )

            following = self._find_next_point(
                lines,
                index,
            )

            if previous not in self.POINT_ORDER:
                continue

            previous_index = (
                self.POINT_ORDER.index(
                    previous
                )
            )

            if (
                previous_index + 1
                >= len(self.POINT_ORDER)
            ):
                continue

            expected = self.POINT_ORDER[
                previous_index + 1
            ]

            if expected not in candidate:
                continue

            if following is not None:
                following_index = (
                    self.POINT_ORDER.index(
                        following
                    )
                )

                expected_index = (
                    self.POINT_ORDER.index(
                        expected
                    )
                )

                if following_index <= expected_index:
                    continue

            replacement = (
                self._replace_ocr_candidate(
                    line,
                    expected,
                )
            )

            if replacement != line:
                lines[index] = replacement

    def _normalize_d_dstroke_points(
        self,
        lines: list[str],
    ) -> None:

        markers = self._collect_markers(
            lines
        )

        for index in range(
            len(markers) - 3
        ):
            group = markers[
                index:index + 4
            ]

            sequence = [
                item["marker"]
                for item in group
            ]

            if sequence == [
                "c",
                "đ",
                "đ",
                "e",
            ]:
                self._replace_point_marker(
                    lines,
                    group[1]["line_index"],
                    "d",
                )

            elif sequence == [
                "c",
                "d",
                "d",
                "e",
            ]:
                self._replace_point_marker(
                    lines,
                    group[2]["line_index"],
                    "đ",
                )

            elif sequence == [
                "c",
                "đ",
                "d",
                "e",
            ]:
                self._replace_point_marker(
                    lines,
                    group[1]["line_index"],
                    "d",
                )

                self._replace_point_marker(
                    lines,
                    group[2]["line_index"],
                    "đ",
                )

        markers = self._collect_markers(
            lines
        )

        if len(markers) < 3:
            return

        last_three = markers[-3:]

        sequence = [
            item["marker"]
            for item in last_three
        ]

        if sequence == [
            "c",
            "đ",
            "đ",
        ]:
            self._replace_point_marker(
                lines,
                last_three[1]["line_index"],
                "d",
            )

        elif sequence == [
            "c",
            "d",
            "d",
        ]:
            self._replace_point_marker(
                lines,
                last_three[2]["line_index"],
                "đ",
            )

        elif sequence == [
            "c",
            "đ",
            "d",
        ]:
            self._replace_point_marker(
                lines,
                last_three[1]["line_index"],
                "d",
            )

            self._replace_point_marker(
                lines,
                last_three[2]["line_index"],
                "đ",
            )

    def _collect_markers(
        self,
        lines: list[str],
    ) -> list[dict]:

        markers = []

        for index, line in enumerate(lines):
            marker = (
                self._extract_point_marker(
                    line
                )
            )

            if marker:
                markers.append(
                    {
                        "line_index": index,
                        "marker": marker,
                    }
                )

        return markers

    def _replace_point_marker(
        self,
        lines: list[str],
        line_index: int,
        new_marker: str,
    ) -> None:

        lines[line_index] = re.sub(
            r"^([ \t]*[._\-|:]*[ \t]*)"
            r"[a-zđ]"
            r"([ \t]*[\)}])",
            rf"\g<1>{new_marker}\g<2>",
            lines[line_index],
            count=1,
            flags=re.IGNORECASE,
        )

    def _find_previous_point(
        self,
        lines: list[str],
        index: int,
    ) -> str | None:

        for position in range(
            index - 1,
            -1,
            -1,
        ):
            marker = (
                self._extract_point_marker(
                    lines[position]
                )
            )

            if marker:
                return marker

        return None

    def _find_next_point(
        self,
        lines: list[str],
        index: int,
    ) -> str | None:

        for position in range(
            index + 1,
            len(lines),
        ):
            marker = (
                self._extract_point_marker(
                    lines[position]
                )
            )

            if marker:
                return marker

        return None

    def _extract_point_marker(
        self,
        line: str,
    ) -> str | None:

        match = re.match(
            r"^[ \t]*"
            r"[._\-|:]*"
            r"[ \t]*"
            r"([a-zđ])"
            r"[ \t]*[\)}]"
            r"[ \t]+",
            line,
            flags=re.IGNORECASE,
        )

        if not match:
            return None

        marker = (
            match.group(1)
            .lower()
            .strip()
        )

        if marker in self.POINT_ORDER:
            return marker

        return None

    def _is_amendment_clause(
        self,
        clause_content: str,
    ) -> bool:

        if not clause_content:
            return False

        head = " ".join(
            clause_content
            .splitlines()[:3]
        ).lower()

        return bool(
            re.search(
                r"sửa\s+(?:đổi|đôi).*?"
                r"(?:bổ|bõ|bd|bỗ|bé)\s+sung",
                head,
                flags=re.IGNORECASE,
            )
        )

    def _protect_nested_amendment_points(
        self,
        clause_content: str,
    ) -> str:

        if not self._is_amendment_clause(
            clause_content
        ):
            return clause_content

        lines = clause_content.splitlines()
        protected = []

        for line in lines:
            if re.match(
                r"^[ \t]*[“”\"*#]+"
                r"[ \t]*"
                r"(?:[a-zđ]|\d+)"
                r"[ \t]*[\)}]",
                line,
                flags=re.IGNORECASE,
            ):
                protected.append(
                    "__NESTED_QUOTE__ " + line
                )
            else:
                protected.append(line)

        return "\n".join(protected)

    def parse_points(
        self,
        clause_content: str,
    ) -> list[dict]:

        if not clause_content:
            return []

        hierarchy_safe_content = (
            self._protect_nested_amendment_points(
                clause_content
            )
        )

        normalized_content = (
            self._normalize_point_ocr(
                hierarchy_safe_content
            )
        )

        matches = list(
            self.POINT_PATTERN.finditer(
                normalized_content
            )
        )

        points = []

        for index, match in enumerate(matches):

            point_letter = (
                match.group(1)
                .strip()
                .lower()
            )

            first_line = (
                match.group(2).strip()
            )

            content_start = match.end()

            content_end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(normalized_content)
            )

            remaining_content = (
                normalized_content[
                    content_start:content_end
                ].strip()
            )

            if remaining_content:
                full_content = (
                    first_line
                    + "\n"
                    + remaining_content
                )
            else:
                full_content = first_line

            points.append(
                {
                    "point": point_letter,
                    "content": full_content.strip(),
                }
            )

        return points

    def validate_point_sequence(
        self,
        points: list[dict],
    ) -> dict:

        letters = [
            str(
                point.get(
                    "point",
                    "",
                )
            ).lower()
            for point in points
        ]

        if not letters:
            return {
                "total_points": 0,
                "duplicate_points": [],
                "unknown_points": [],
                "missing_points": [],
                "out_of_order": [],
            }

        counts = Counter(letters)

        duplicates = [
            letter
            for letter, count
            in counts.items()
            if count > 1
        ]

        unknown = [
            letter
            for letter in letters
            if letter not in self.POINT_ORDER
        ]

        known = [
            letter
            for letter in letters
            if letter in self.POINT_ORDER
        ]

        missing = []

        if known:
            indexes = [
                self.POINT_ORDER.index(
                    letter
                )
                for letter in known
            ]

            start = min(indexes)
            end = max(indexes)

            expected = (
                self.POINT_ORDER[
                    start:end + 1
                ]
            )

            missing = [
                letter
                for letter in expected
                if letter not in known
            ]

        out_of_order = []

        for index in range(
            1,
            len(known),
        ):
            previous = known[index - 1]
            current = known[index]

            previous_index = (
                self.POINT_ORDER.index(
                    previous
                )
            )

            current_index = (
                self.POINT_ORDER.index(
                    current
                )
            )

            if (
                current_index
                <= previous_index
            ):
                out_of_order.append(
                    {
                        "previous": previous,
                        "current": current,
                        "position": index,
                    }
                )

        return {
            "total_points": len(points),
            "duplicate_points": duplicates,
            "unknown_points": unknown,
            "missing_points": missing,
            "out_of_order": out_of_order,
        }

    def _join_title_lines(
        self,
        lines: list[str],
    ) -> str:

        result = []

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if self._is_noise_line(line):
                continue

            result.append(line)

        title = " ".join(result)

        title = re.sub(
            r"\s+",
            " ",
            title,
        )

        return title.strip()

    def _is_noise_line(
        self,
        line: str,
    ) -> bool:

        if not line:
            return True

        if self.OCR_NOISE_PATTERN.fullmatch(
            line
        ):
            return True

        if re.fullmatch(
            r"\d{1,3}",
            line,
        ):
            return True

        return False

    def get_article(
        self,
        articles: list[dict],
        article_number: str | int,
    ) -> dict | None:

        target = str(
            article_number
        ).lower()

        for article in articles:
            current = str(
                article.get(
                    "article_number",
                    "",
                )
            ).lower()

            if current == target:
                return article

        return None

    def validate_article_sequence(
        self,
        articles: list[dict],
    ) -> dict:

        numbers = []

        for article in articles:
            number = str(
                article.get(
                    "article_number",
                    "",
                )
            )

            if number.isdigit():
                numbers.append(
                    int(number)
                )

        if not numbers:
            return {
                "total_articles": len(
                    articles
                ),
                "first_article": None,
                "last_article": None,
                "missing_articles": [],
                "duplicate_articles": [],
                "out_of_order": [],
            }

        counts = Counter(numbers)

        duplicates = sorted(
            number
            for number, count
            in counts.items()
            if count > 1
        )

        first_article = min(numbers)
        last_article = max(numbers)

        existing = set(numbers)

        missing = [
            number
            for number in range(
                first_article,
                last_article + 1,
            )
            if number not in existing
        ]

        out_of_order = []

        for index in range(
            1,
            len(numbers),
        ):
            previous = numbers[
                index - 1
            ]

            current = numbers[index]

            if current != previous + 1:
                out_of_order.append(
                    {
                        "previous": previous,
                        "current": current,
                        "position": index,
                    }
                )

        return {
            "total_articles": len(
                articles
            ),
            "first_article": first_article,
            "last_article": last_article,
            "missing_articles": missing,
            "duplicate_articles": duplicates,
            "out_of_order": out_of_order,
        }

    def validate_clause_sequence(
        self,
        clauses: list[dict],
    ) -> dict:

        numbers = []

        for clause in clauses:
            number = str(
                clause.get(
                    "clause_number",
                    "",
                )
            )

            if number.isdigit():
                numbers.append(
                    int(number)
                )

        if not numbers:
            return {
                "total_clauses": 0,
                "first_clause": None,
                "last_clause": None,
                "starts_with_one": None,
                "missing_clauses": [],
                "duplicate_clauses": [],
                "out_of_order": [],
            }

        counts = Counter(numbers)

        duplicates = sorted(
            number
            for number, count
            in counts.items()
            if count > 1
        )

        first = min(numbers)
        last = max(numbers)

        existing = set(numbers)

        missing = [
            number
            for number in range(
                first,
                last + 1,
            )
            if number not in existing
        ]

        out_of_order = []

        for index in range(
            1,
            len(numbers),
        ):
            previous = numbers[
                index - 1
            ]

            current = numbers[index]

            if current != previous + 1:
                out_of_order.append(
                    {
                        "previous": previous,
                        "current": current,
                        "position": index,
                    }
                )

        return {
            "total_clauses": len(
                clauses
            ),
            "first_clause": numbers[0],
            "last_clause": numbers[-1],
            "starts_with_one": (
                numbers[0] == 1
            ),
            "missing_clauses": missing,
            "duplicate_clauses": duplicates,
            "out_of_order": out_of_order,
        }