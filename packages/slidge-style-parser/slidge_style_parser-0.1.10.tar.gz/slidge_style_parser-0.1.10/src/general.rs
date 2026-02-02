use std::collections::HashMap;

use pyo3::prelude::*;

use crate::parser::parse_with_limits;

#[pyfunction]
pub fn format_body(body: String, new_tags: HashMap<String, (String, String)>) -> PyResult<String> {
    let mut chars: Vec<char> = body.chars().collect();
    if chars.len() < 1 {
        return Ok(body);
    }
    let styles: Vec<(String, usize, usize, usize, usize)> = parse_with_limits(&chars, 0, chars.len() - 1, 0);
    let parse_quotes = new_tags.contains_key(&">".to_string());

    let mut tags: Vec<(usize, String, usize)> = Vec::with_capacity(styles.len() * 2);
    for (keyword, start, remove_start, end, remove_end) in styles {
        if new_tags.contains_key(&keyword) {
            let opening_tag = if keyword == "```language" {
                new_tags.get(&keyword).unwrap().0.clone()
                .replace("{}", &chars[start+3..remove_start-1]
                .into_iter()
                .collect::<String>())
            } else {
                new_tags.get(&keyword).unwrap().0.clone()
            };
            tags.push((start, opening_tag, remove_start));
            tags.push((end, new_tags.get(&keyword).unwrap().1.clone(), remove_end));
        } else if (keyword == ">>" && parse_quotes) || keyword == "```>" || keyword == "\\" {
            tags.push((start, "".to_string(), start+1));
        }
    }

    tags.sort_by(|a, b| b.0.cmp(&a.0));

    for (index, tag, end) in tags {
        chars = [chars[..index].to_vec(), tag.chars().collect(), chars[end..].to_vec()].concat();
    }

    let text: String = if new_tags.contains_key("\n") {
        chars.into_iter().collect::<String>().replace("\n", &new_tags.get(&"\n".to_string()).unwrap().0)
    } else {
        chars.into_iter().collect::<String>()
    };

    Ok(text)
}
