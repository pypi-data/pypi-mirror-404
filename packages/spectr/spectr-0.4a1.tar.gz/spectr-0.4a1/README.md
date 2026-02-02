<div align="center">
  <h1>Spectr</h1>
  <p>
    A terminal user interface (TUI) for browsing, previewing, and managing data files created by <a href="https://www.qass.net/en">QASS</a> Analyzer4D software.
  </p>
</div>

<div align="center">
  <img src="assets/demo.gif" alt="Demo recording showing file preview functionality"/>
  <p>
    <sub>Demo using the <code>catppuccin-mocha</code> theme</sub>
  </p>
</div>

## Features

- Browse and preview Analyzer4D data files directly in your terminal
- Customizable table columns and sorting
- Multiple plot marker styles with configurable downsampling
- Flexible file filtering with glob and regex patterns
- Theming support

## Installation

Install Spectr as a standalone tool using [uv](https://github.com/astral-sh/uv):
```sh
uv tool install spectr
```

Or run it directly without installing:
```sh
uvx spectr --help
```

## Usage

By default, Spectr scans the current working directory recursively for files matching Analyzer4D's standard naming conventions:
```sh
spectr
```

To scan a specific directory:
```sh
spectr --path /path/to/data
```

To use custom file patterns:
```sh
spectr --glob-pattern "*.dat" --regex-pattern "your_pattern"
```

> **Note:** Scanning directories with many files may take some time.

## Configuration

Spectr uses a TOML configuration file located at `~/.config/spectr/config.toml`.

### Example Configuration
```toml
[table]
columns = ["process", "compression_time", "compression_frq", "avg_time", "avg_frq"]

[table.sort]
attribute = "process"
order = "ASC"  # or "DESC"

[plot]
marker = "braille"           # options: "braille", "fhd", "hd", "dot"
displayed_datapoints = 1000
downsampling = "lttb"        # options: "lttb", "max_bucket"

[stats]
attributes = [
  "project_id", "directory_path", "filename", "process", "channel",
  "datamode", "datakind", "datatype", "process_time", "process_date_time",
  "db_header_size", "bytes_per_sample", "db_count", "full_blocks",
  "db_size", "db_sample_count", "frq_bands", "db_spec_count",
  "compression_frq", "compression_time", "avg_time", "avg_frq",
  "spec_duration", "frq_start", "frq_end", "frq_per_band",
  "sample_count", "spec_count", "adc_type", "bit_resolution",
  "fft_log_shift", "streamno", "preamp_gain", "analyzer_version", "partnumber"
]

[metadata_cache]
sync_recursive = true   # currently unused
persist_cache = false
```

All `table.columns` and `stats.attributes` values correspond to attributes from the `qass.tools.analyzer.buffer_metadata.BufferMetadata` object.

## Contributing

Contributions are welcome! The current focus is on improving core features—preview, filtering, and copying—to make them more user-friendly and robust. If you have ideas for improving the user experience, please open an issue.

### Roadmap

- [ ] Async or paginated table creation (large query results currently cause temporary unresponsiveness)
- [ ] Improved copy screen UX
  - [ ] Text input for path entry
  - [ ] Preselect current working directory in directory tree
  - [ ] Async conflict calculation
- [ ] Persist selected theme

## License

[GNU Lesser General Public License v3.0](LICENSE)

## Acknowledgments

Built on top of [qass-tools-analyzer](https://github.com/QASS/qass-tools-analyzer) by [QASS GmbH](https://www.qass.net/en), which provides the core functionality for reading and organizing Analyzer4D files.
