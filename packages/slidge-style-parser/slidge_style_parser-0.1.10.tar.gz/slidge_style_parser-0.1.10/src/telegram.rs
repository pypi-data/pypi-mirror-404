use pyo3::prelude::*;

use crate::parser::parse_with_limits;

const TELEGRAM_STYLES: &[(&'static str, &'static str)] = &[
    ("_", "italics"),
    ("*", "bold"),
    ("~", "strikethrough"),
    ("||", "spoiler"),
    ("`", "code"),
    ("```language", "pre"),
    ("```", "pre")
];

#[pyfunction]
pub fn format_for_telegram(body: String, mentions: Option<Vec<(String, usize, usize)>>) -> PyResult<(String, Vec<(String, usize, usize, String)>)> {
    let mut chars: Vec<char> = body.chars().collect();
    if chars.len() < 1 {
        return Ok((body, Vec::with_capacity(0)));
    }
    let mentions = mentions.unwrap_or(Vec::with_capacity(0));

    let styles: Vec<(String, usize, usize, usize, usize)> = parse_with_limits(&chars, 0, chars.len() - 1, 0);
    let mut remove_tags: Vec<(usize, usize)> = Vec::with_capacity(styles.len() * 2);
    for (keyword, start, remove_start, end, remove_end) in &styles {
        if TELEGRAM_STYLES.iter().any(|&(k, _)| k == keyword) {
            remove_tags.push((*start, *remove_start));
            remove_tags.push((*end, *remove_end));
        } else if keyword == "```>" || keyword == "\\" {
            remove_tags.push((*start, *remove_start));
        }
    }

    // is_start (*<-- start, end -->*), index of all_indexes, format, index of tag, language of codeblock
    let mut message_entities: Vec<(bool, usize, String, usize, String)> = Vec::with_capacity(styles.len() * 2);
    let mut all_indexes: Vec<Vec<usize>> = Vec::with_capacity(styles.len());
    for (keyword, start, remove_start, end, remove_end) in &styles {
        if TELEGRAM_STYLES.iter().any(|&(k, _)| k == keyword) {
            let language = if keyword == "```language" {
                chars[start+3..remove_start-1]
                .into_iter()
                .collect::<String>()
            } else {
                String::new()
            };
            all_indexes.push(vec![*start, *remove_start - *start, *end, *remove_end - *end]);
            let last_index = all_indexes.len() - 1;
            message_entities.push((true, last_index, TELEGRAM_STYLES.iter().find(|&&(k, _)| k == keyword).unwrap().1.to_owned(), *start, language));
            message_entities.push((false, last_index, String::new(), *end, String::new()));
        } else if keyword == "```>" || keyword == "\\" {
            all_indexes.push(vec![0, 0, *start, 1]);
            message_entities.push((false, all_indexes.len() - 1, String::new(), *start, String::new()));
        }
    }
    for (_name, start, end) in mentions {
        all_indexes.push(vec![start, 0, end, 0]);
        let last_index = all_indexes.len() - 1;
        message_entities.push((true, last_index, "mention".to_owned(), start, String::new()));
        message_entities.push((false, last_index, String::new(), end, String::new()));
    }
    message_entities.sort_by(|a, b| a.3.cmp(&b.3));

    remove_tags.sort_by(|a, b| b.0.cmp(&a.0));

    for (index, end) in remove_tags {
        chars = [chars[..index].to_vec(), chars[end..].to_vec()].concat();
    }

    let formatted_text = chars.into_iter().collect::<String>();
    let utf16_lengths: Vec<usize> = utf8_to_utf16_length(&formatted_text);

    let mut offset = 0;
    for (is_start, index, _, _, _) in &message_entities {
        let indexes = &mut all_indexes[*index];
        if *is_start {
            indexes[0] -= offset;
            offset += indexes[1];
        } else {
            indexes[2] -= offset;
            offset += indexes[3];
        }
    }
    Ok((
        formatted_text,
        message_entities.into_iter()
            .filter(|(is_start, _, _, _, _)| { *is_start } )
            .map(|(_, index, format, _, language)| { (format, utf16_lengths[all_indexes[index][0]], utf16_lengths[all_indexes[index][2]] - utf16_lengths[all_indexes[index][0]], language) })
            .collect()
    ))
}

fn utf8_to_utf16_length(utf8_str: &str) -> Vec<usize> {
    let mut utf16_lengths = Vec::with_capacity(utf8_str.len());

    let mut length = 0;
    utf16_lengths.push(0);
    for byte in utf8_str.as_bytes() {
        if (byte & 0xc0) != 0x80 {
            length += if *byte >= 0xf0 { 2 } else { 1 };
            utf16_lengths.push(length);
        }
    }
    utf16_lengths
}
