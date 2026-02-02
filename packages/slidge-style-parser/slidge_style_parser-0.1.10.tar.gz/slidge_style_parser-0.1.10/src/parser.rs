const KEYWORDS: [char; 4] = ['*', '_', '~', '`'];
const NO_SUB_PARSING_KEYWORDS: [char; 1] = ['`'];
const QUOTE_KEYWORDS: [char; 1] = ['>'];

pub fn parse_with_limits(chars: &Vec<char>, start: usize, end: usize, depth: usize) -> Vec<(String, usize, usize, usize, usize)> {
    let mut styles = Vec::new();
    let mut index = start;
    let end = end.min(chars.len() - 1);

    while index <= end {
        let c = chars[index];
        if c == '\\' {
            styles.push(("\\".to_owned(), index, index + 1, index + 1, index + 1));
            index += 2;
            continue;
        }

        if QUOTE_KEYWORDS.contains(&c) {
            if is_quote_start(chars, index, depth) {
                let to = seek_end_of_quote(chars, index, end, depth);
                styles.push((">".to_owned(), index, index + 1, to, to));
                styles.append(&mut parse_with_limits(chars, index + 1, to, depth + 1));
                index = to;
                continue;
            } else if is_nested_quote(chars, index, depth) {
                styles.push((">>".to_owned(), index, index + 1, index + 1, index + 1));
            } else {
                styles.push(("&gt;".to_owned(), index, index + 1, index + 1, index + 1));
            }
            index += 1;
            continue;
        }

        if c == '<' {
            styles.push(("&lt;".to_owned(), index, index + 1, index + 1, index + 1));
            index += 1;
            continue;
        }

        if c == '`' && is_char_repeating(chars, c, 2, index + 1, end) {
            let end_of_line = seek_end_of_line(chars, index + 1, end);
            if end_of_line == end {
                index += 3;
                continue;
            }
            match seek_end_block(chars, c, end_of_line, end, depth) {
                Some(to) => {
                    if to != end_of_line && is_quote_start(chars, index, depth) {
                        let keyword = if end_of_line == index + 3 {
                            "```".to_owned()
                        } else {
                            "```language".to_owned()
                        };
                        let remove_end = if depth > 0 && (to == end || to == chars.len()) {
                            to
                        } else {
                            to + 4 + depth
                        };
                        styles.push((keyword, index, end_of_line + 1, to, remove_end));
                        styles.append(&mut parse_quotes_in_code_block(chars, index + 3, to, depth));
                        index = to;
                    }
                }
                None => ()
            }
            index += 3;
            continue;
        }

        if !preceeded_by_whitespace(chars, index, start) || followed_by_whitespace(chars, index, end) {
            index += 1;
            continue;
        }

        if c == '|' && is_char_repeating(chars, c, 1, index + 1, end) {
            match seek_end(chars, c, index + 2, 1, end) {
                Some(to) => {
                    if to != index + 2 {
                        let keyword = "||".to_owned();
                        styles.push((keyword, index, index + 2, to, to + 2));
                        styles.append(&mut parse_with_limits(chars, index + 2, to - 1, depth));
                    }
                    index = to + 2;
                    continue;
                }
                None => ()
            }
            index += 2;
            continue;
        }

        if !KEYWORDS.contains(&c) {
            index += 1;
            continue;
        }

        match seek_end(chars, c, index + 1, 0, end) {
            Some (to) => {
                if to != index + 1 {
                    styles.push((c.to_string(), index, index + 1, to, to + 1));
                    if !NO_SUB_PARSING_KEYWORDS.contains(&c) {
                        styles.append(&mut parse_with_limits(chars, index + 1, to - 1, depth));
                    }
                }
                index = to + 1;
            }
            None => ()
        }
        index += 1;
    }
    styles
}

fn parse_quotes_in_code_block(chars: &Vec<char>, start: usize, end: usize, depth: usize) -> Vec<(String, usize, usize, usize, usize)> {
    let mut quotes = Vec::new();
    let mut index = start;
    let end = end.min(chars.len() - 1);

    if depth < 1 {
        return quotes;
    }

    while index <= end {
        let c = chars[index];
        if QUOTE_KEYWORDS.contains(&c) {
            if is_nested_quote(chars, index, depth) {
                quotes.push(("```>".to_owned(), index, index + 1, index + 1, index + 1));
            }
            index += 1;
            continue;
        }
        index += 1;
    }
    quotes
}

fn is_nested_quote(chars: &Vec<char>, start: usize, depth: usize) -> bool {
    let mut index = start;
    let mut count = 0;

    while index > 0 {
        if chars[index] == '\n' {
            return true;
        }
        if !QUOTE_KEYWORDS.contains(&chars[index]) {
            return false;
        }
        count += 1;
        if count > depth {
            return false;
        }
        index -= 1;
    }
    true
}

fn is_char_repeating(chars: &Vec<char>, keyword: char, repetitions: usize, index: usize, end: usize) -> bool {
    (0..repetitions as usize)
        .all(|i| index + i <= end && chars[index + i] == keyword)
}

fn preceeded_by_whitespace(chars: &Vec<char>, index: usize, start: usize) -> bool {
    index == start || chars[index - 1].is_whitespace()
}

fn followed_by_whitespace(chars: &Vec<char>, index: usize, end: usize) -> bool {
    index >= end || chars[index + 1].is_whitespace()
}

fn seek_end(chars: &Vec<char>, keyword: char, start: usize, repetitions: usize, end: usize) -> Option<usize> {
    for i in start..=end {
        let c = chars[i];
        if c == '\n' {
            return None;
        }
        if c == keyword
            && !chars[i - 1].is_whitespace()
            && is_char_repeating(chars, keyword, repetitions, i + 1, end)
        {
            match seek_higher_order_end(chars, c, i + 1, end) {
                Some(higher_order_i) => {
                    return Some(higher_order_i);
                }
                None => {
                    return Some(i);
                }
            }
        }
    }
    None
}

fn seek_higher_order_end(chars: &Vec<char>, keyword: char, start: usize, end: usize) -> Option<usize> {
    let mut skip = true;
    for i in start..=end {
        let c = chars[i];
        if c == '\n' {
            return None;
        }
        if c != keyword {
            skip = false;
            continue;
        }
        if chars[i - 1].is_whitespace() && !followed_by_whitespace(chars, i, end) {
            return None; // "*bold* *<--- beginning of new bold>*"
        }
        if followed_by_whitespace(chars, i, end) && !skip {
            return Some(i);
        }
    }
    None
}

fn seek_end_of_line(chars: &Vec<char>, start: usize, end: usize) -> usize {
    chars[start..=end]
        .iter()
        .enumerate()
        .find(|&(_, &c)| c == '\n')
        .map_or(end + 1, |(i, _)| start + i)
}

fn seek_end_of_quote(chars: &Vec<char>, start: usize, end: usize, depth: usize) -> usize {
    for i in start..=end {
        if chars[i] == '\n' {
            if i + 2 + depth > chars.len() {
                return i;
            }
            if chars[i + 1..=i + 1 + depth].iter().any(|&c| !QUOTE_KEYWORDS.contains(&c)) {
                return i;
            }
        }
    }
    end + 1
}

fn seek_end_block(chars: &Vec<char>, keyword: char, start: usize, end: usize, depth: usize) -> Option<usize> {
    for i in start..=end {
        if chars[i] == '\n' {
            if i + depth == end && chars[i + 1..i + 1 + depth].iter().all(|&c| QUOTE_KEYWORDS.contains(&c)) {
                continue;
            }
            if i + 1 + depth > end {
                return Some(i);
            }
            if seek_end_of_line(chars, i + 1, end) == i + depth + 4
                && chars[i + 1..i + 1 + depth].iter().all(|&c| QUOTE_KEYWORDS.contains(&c))
                && chars[i + 1 + depth] == keyword
                && is_char_repeating(chars, keyword, 2, i + 1 + depth, end)
            {
                return Some(i);
            }
        }
    }
    if end == chars.len() - 1 {
        if depth == 0 {
            return None;
        }
        return Some(chars.len());
    }
    Some(end)
}

fn is_quote_start(chars: &Vec<char>, index: usize, depth: usize) -> bool {
    index - depth == 0 || chars[index - 1 - depth] == '\n'
}
