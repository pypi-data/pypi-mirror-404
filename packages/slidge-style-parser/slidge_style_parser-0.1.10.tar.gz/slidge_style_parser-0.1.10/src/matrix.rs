use pyo3::prelude::*;

use crate::parser::parse_with_limits;

const DUAL_TAGS: &[(&'static str, (&'static str, &'static str))] = &[
    ("_", ("<em>", "</em>")),
    ("*", ("<strong>", "</strong>")),
    ("~", ("<s>", "</s>")),
    ("`", ("<code>", "</code>")),
    ("```", ("<pre><code>", "</code></pre>")),
    ("```language", ("<pre><code class=\"language-{}\">", "</code></pre>")),
    (">", ("<blockquote>", "</blockquote>")),
    ("||", ("<span data-mx-spoiler>", "</span>")),
];

const SINGLE_TAGS: &[(&'static str, &'static str)] = &[
    (">>", ""),
    ("```>", ""),
    ("\\", ""),
    ("&lt;", "&lt;"),
    ("&gt;", "&gt;"),
];

#[pyfunction]
pub fn format_for_matrix(body: String, mentions: Option<Vec<(String, usize, usize)>>) -> PyResult<String> {
    let mut chars: Vec<char> = body.chars().collect();
    if chars.len() < 1 {
        return Ok(body);
    }
    let mentions = mentions.unwrap_or(Vec::with_capacity(0));

    let styles: Vec<(String, usize, usize, usize, usize)> = parse_with_limits(&chars, 0, chars.len() - 1, 0);
    let mut tags: Vec<(usize, String, usize)> = Vec::with_capacity(styles.len() * 2);
    for (keyword, start, remove_start, end, remove_end) in styles {
        if DUAL_TAGS.iter().any(|&(k, _)| k == keyword) {
            let opening_tag = if keyword == "```language" {
                DUAL_TAGS.iter().find(|&&(k, _)| k == keyword).unwrap().1.0
                .replace("{}", &chars[start+3..remove_start-1]
                .into_iter()
                .collect::<String>())
            } else {
                DUAL_TAGS.iter().find(|&&(k, _)| k == keyword).unwrap().1.0.to_owned()
            };
            tags.push((start, opening_tag, remove_start));
            tags.push((end, DUAL_TAGS.iter().find(|&&(k, _)| k == keyword).unwrap().1.1.to_owned(), remove_end));
        } else if SINGLE_TAGS.iter().any(|&(k, _)| k == keyword) {
            tags.push((start, SINGLE_TAGS.iter().find(|&&(k, _)| k == keyword).unwrap().1.to_owned(), start+1));
        }
    }
    for (mxid, start, end) in mentions {
        tags.push((start, "<a href='https://matrix.to/#/".to_owned() + &mxid + "'>", start));
        tags.push((end, "</a>".to_owned(), end));
    }

    tags.sort_by(|a, b| b.0.cmp(&a.0));

    let mut replace_newlines_to = chars.len();
    for (index, tag, end) in tags {
        if tag == "</code></pre>" {
            // index is at \n, add 1 to skip that one
            let substring = chars[index + 1..replace_newlines_to].into_iter().collect::<String>();
            chars = [&chars[..index + 1], &substring.replace('\n', "<br>").chars().collect::<Vec<char>>()[..], &chars[replace_newlines_to..]].concat();
        } else if tag.starts_with("<pre>") {
            replace_newlines_to = index;
        }

        let tag: Vec<char> = tag.chars().collect();
        chars = [chars[..index].to_vec(), tag.clone(), chars[end..].to_vec()].concat();
        
        let offset: isize = index as isize - end as isize + tag.len() as isize;
        replace_newlines_to = if offset > 0 {
            replace_newlines_to + offset as usize
        } else {
            replace_newlines_to - offset.abs() as usize
        };
    }
    let substring = chars[..replace_newlines_to].into_iter().collect::<String>();
    let text = [substring.replace('\n', "<br>"), chars[replace_newlines_to..].into_iter().collect::<String>()].concat();

    Ok(text)
}
