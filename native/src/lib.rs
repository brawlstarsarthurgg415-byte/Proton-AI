#[cfg(test)]
mod tests {
    #[test]
    fn curriculum_has_multiple_subjects() {
        let source = include_str!("main.rs");
        for subject in ["Programacao", "Astronomia", "Historia", "Geografia", "Ingles"] {
            assert!(source.contains(subject));
        }
    }
}
