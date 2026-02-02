━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ❗ 𝗜𝗠𝗣𝗢𝗥𝗧𝗔𝗡𝗧 𝗡𝗢𝗧𝗜𝗖𝗘

**Your use of this Software in any form constitutes your acceptance of this Agreement.**

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

---

>>pip install Qarvexium
>>>Run this so u can use the library. 

```bash
pip install Qarvexium
```

---
>External means that the required files to be downloaded from Github
---

---
>External files are essential but NOT required for functions that doesnt contain External Tag
---

---
>Why the file size is so big? (9gb) Because it contains LLM (Large Language Model)s, Executeables, DLL (Dynamic Link Library)s.
>Can i Delete the unnecessary files? Yes you can. Every external function requires its own spesific file and nothing else.
---

## ExtrasManager — Split ZIP Dependency Manager

> Purpose\
> Manages multi-part ZIP dependencies, supporting discovery, download, assembly, and extraction.

> > Initialization
> >
> > - Resolves the package root directory
> > - Defines standard paths for ZIP, parts, and extraction
> > - Supports configurable parallel download workers

> > ZIP Validation
> >
> > - Verifies ZIP integrity before extraction
> > - Detects corrupted or incomplete archives

> > Local Part Discovery
> >
> > - Scans for numbered ZIP fragments
> > - Orders parts deterministically
> > - Supports partial or complete local availability

> > Download System
> >
> > - Supports resumable HTTP downloads
> > - Uses ranged requests when possible
> > - Displays live progress and transfer speed
> > - Downloads parts concurrently

> > Assembly Process
> >
> > - Concatenates ZIP parts in correct order
> > - Validates the assembled archive
> > - Cleans up part files after successful assembly

> > Extraction
> >
> > - Extracts dependencies into the package root
> > - Prevents redundant extraction if already installed

> > Installation Workflow
> >
> > - Uses local ZIP if valid
> > - Assembles from local parts if present
> > - Falls back to remote downloads if required

## OCR — OCR Executor (External)

> Purpose
> A lightweight wrapper around an external OCR executable (ocr_tool.exe).

> > Initialization
> >
> > * Accepts a path to an OCR executable
> > * Automatically resolves relative path inside extras/
> > * Raises FileNotFoundError if the executable is missing

> > Execution (run)
> >
> > * Runs OCR on an optional image file
> > * Supports GPU acceleration
> > * Supports detailed output mode
> > * Allows minimum confidence filtering
> > * Optional timeout control
> > * Returns raw stdout as a string

---

## Klap — Native Keyboard Event Engine (DLL,External)

> Purpose
> Interfaces with Klap.dll to capture and react to low-level keyboard events.

> > Initialization
> >
> > * Loads native DLL via ctypes
> > * Defines argument and return types for all exported functions
> > * Initializes internal state for key tracking, patterns, and callbacks
> > * Automatically installs an internal keyboard callback

> > Core Capabilities
> >
> > * Detect key press and release events
> > * Track currently pressed keys
> > * Detect key combinations (combos)
> > * Detect ordered key patterns (macros)
> > * Support raw low-level event callbacks
> > * Simplify the keys on demand

> > Event Systems
> >
> > * Keypress Handlers: triggered when a specific key is pressed
> > * Combo Handlers: triggered when multiple keys are held simultaneously
> > * Pattern Handlers: triggered when a sequence of key actions occurs

> > Process Control
> >
> > * Can spawn an external Klap executable
> > * Graceful termination with timeout fallback
> > * Supports context-manager usage

> > Connection Control
> >
> > * Connect and disconnect
> > * Start and stop
> > * Connection status querying

---

## Findify — Native File Finder (DLL,External)

> Purpose
> Simple Python interface to Findify.dll for fast native file lookup.

> > Initialization
> >
> > * Loads Findify.dll
> > * Defines argument and return types for findify

> > File Search
> >
> > * Accepts a filename
> > * Returns a resolved path as string
> > * Returns None if no match is found
> > * Uses platform-native encoding

---

## Intent — Natural Language Command Engine

> Purpose
> A declarative intent system that maps natural language commands to Python functions.

> > Core Concept
> >
> > * Define command patterns with placeholders
> > * Automatically parse parameters
> > * Execute bound Python functions
> > * Optional confirmation and debug modes

### IntentMatcher — Internal Engine

> Pattern Registration
>
> > * Register commands using text patterns
> > * Supports typed placeholders
> > * Auto-generates regex from function signatures

> Supported Parameter Types
>
> > * int
> > * float
> > * datetime
> > * time
> > * str (default fallback)

> Parsing and Execution
>
> > * Matches full commands case-insensitively
> > * Converts extracted parameters to correct types
> > * Optional confirmation before execution
> > * Debug mode for tracing execution flow

> Error Handling
>
> > * Fuzzy matching suggestions for unknown commands
> > * Graceful failure with readable messages

> Help System
>
> > * Lists all registered commands
> > * Displays descriptions, parameters, and confirmation flags
> > * Supports keyword filtering

### Intent — Public API

> Usage
>
> > * Register intents via decorator or direct call
> > * Execute commands by calling the instance
> > * Enable help and debug modes
> > * Parse commands without executing if needed

---

## Environment — Runtime Context Detector

> Purpose
> Collects and normalizes runtime environment metadata.

> > Detected Information
> >
> > * Environment type (production, development, testing, ci)
> > * Docker detection
> > * Virtualenv detection
> > * Operating system and version
> > * Python version
> > * Machine architecture
> > * Hostname

> > Environment Resolution Logic
> >
> > * Reads ENV or ENVIRONMENT variables
> > * Detects CI platforms automatically
> > * Defaults to development

> > Convenience Properties
> >
> > * env
> > * is_docker
> > * is_virtualenv
> > * is_production
> > * is_development
> > * is_testing

> > Snapshot Access
> >
> > * info() returns a copy of all detected metadata


---

## AudioRecorder — Native Audio Capture (DLL,External)

> Purpose  
> Provides a Python interface to a native audio recording DLL for capturing raw audio samples.

>> Initialization
>> - Searches for the audio recorder DLL across multiple candidate paths
>> - Loads the DLL via ctypes once found
>> - Optionally logs the resolved DLL path
>> - Defines argument and return types for all exported recorder functions
>> - Raises detailed errors if the DLL cannot be found or loaded

>> Recording (rec)
>> - Initializes the recorder with sample rate, channel count, and duration
>> - Supports only int16 audio format
>> - Starts and stops recording automatically
>> - Blocks for the required recording duration
>> - Retrieves recorded samples into a Python array
>> - Cleans up native resources after recording

>> Lifecycle Management
>> - Tracks initialization state internally
>> - Ensures native cleanup on object destruction

---

## QllmClient — Local LLM Socket Client (External)

> Purpose  
> A TCP client for communicating with a local LLM server over a custom binary protocol.

>> Connection Management
>> - Connects to a local server at a fixed address and port
>> - Performs a magic handshake to validate the protocol
>> - Optionally sends a system prompt during connection setup
>> - Maintains connection state internally

>> Message Exchange
>> - Sends UTF-8 encoded user messages
>> - Associates each request with a UUID
>> - Reads exact-length binary responses from the socket
>> - Verifies response UUIDs against request IDs
>> - Returns response text and request identifier

>> Error Handling
>> - Detects disconnected or closed sockets
>> - Raises communication errors on protocol failure
>> - Logs warnings for request ID mismatches

>> Prompt Presets
>> - Provides a catalog of predefined system prompts
>> - Includes stylistic, professional, role-based, and experimental personas
>> - Allows easy switching of assistant behavior

>> Resource Management
>> - Supports explicit connection close
>> - Implements context-manager protocol for automatic cleanup

---

## fpath — Flexible Path Resolver and Validator

> Purpose\
> Resolves, validates, and optionally materializes filesystem paths with sandboxing, download, and executability checks.

> > Path Resolution
> >
> > - Expands environment variables and user home
> > - Normalizes path separators
> > - Resolves relative paths against the package base directory

> > Remote Resource Handling
> >
> > - Detects HTTP and HTTPS URLs
> > - Downloads remote content to a temporary file
> > - Infers file extension from MIME type
> > - Returns a resolved temporary path

> > Extension Handling
> >
> > - Enforces a required file extension if provided
> > - Automatically appends or replaces suffixes

> > Directory and File Validation
> >
> > - Can enforce directory-only or file-only paths
> > - Supports mandatory existence checks
> > - Optional automatic directory creation

> > Executable Validation
> >
> > - Verifies path existence
> > - Enforces executable permissions
> > - Validates Windows executable suffix requirements

> > Sandboxing
> >
> > - Prevents path traversal outside the package base directory
> > - Raises explicit errors on sandbox escape attempts

---

## fsearch — File Prefix Search Utility

> Purpose\
> Searches a directory for files matching a name prefix.

> > Search Behavior
> >
> > - Operates on a resolved directory path
> > - Supports shallow or recursive traversal
> > - Filters only regular files
> > - Returns sorted results

> > Error Handling
> >
> > - Raises if the base path does not exist
> > - Raises if the base path is not a directory
> > - Optionally enforces at least one match

---