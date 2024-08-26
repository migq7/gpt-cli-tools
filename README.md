# Command List
Content is temporarily unavailable outside of Feishu Document

## Quick Start

### 1. Configuration Initialization
Run the following command on the server 192.168.4.27. If you see the output below, the initialization is successful:

```bash
~ > shistGPT --init
[info] config.yaml created successfully
```

### 2. Start a New Conversation
Run the following command:

```bash
~ > saskGPT Tell me about C++
```

The terminal will display the following output:

```
╭─ askGPT | gpt-4o-mini ───────────────────────────────────────────╮
│ Tell me about C++                                               │
╰──────────────────────────────────────────────────────────────────╯
C++ is a general-purpose programming language developed by Bjarne Stroustrup in 1979. It is based on the C language and
adds object-oriented features such as classes and inheritance. C++ supports multiple programming paradigms, including
procedural, object-oriented, and generic programming. Additionally, C++ provides a powerful standard library and is
widely used in system software, game development, embedded systems, and more. Due to its high performance and
flexibility, C++ remains the language of choice for many developers.
───────────────────── 2024 July 30 - 09:17 PM ──────────────────────
```

### 3. Continue the Previous Conversation
Run the following command:

```bash
~ > smoreGPT Tell me more
```

The terminal will display the following output:

```
╭─ askGPT | gpt-4o-mini ───────────────────────────────────────────╮
│ Tell me more                                                   │
╰──────────────────────────────────────────────────────────────────╯
C++ is a statically typed, compiled language with several key features:

1. **Object-Oriented Programming**: C++ supports encapsulation, inheritance, and polymorphism, allowing developers to
create reusable and modular code.

2. **Generic Programming**: Through templates, C++ supports the creation of generic functions and classes, making code
more flexible and reusable.

3. **Memory Management**: C++ allows developers to manually control memory usage through pointers and dynamic memory
allocation, providing efficient resource management, but also requiring careful coding to avoid memory leaks or errors.

4. **Standard Template Library (STL)**: STL provides a powerful set of template classes and algorithms supporting common
data structures (like vectors, lists, sets) and algorithms (like sorting, searching), thus improving programming
efficiency.

5. **Cross-Platform Capability**: C++ can be compiled and run on various operating systems and platforms, making
applications developed in it easily portable.

C++ is widely used in game development (e.g., Unreal Engine), high-performance computing (e.g., numerical simulations),
graphics processing, operating systems, and large system software, favored for its fine control over hardware and
efficient execution.
───────────────────── 2024 July 30 - 09:18 PM ──────────────────────
```

### 4. View History / Continue Historical Conversations
Run the following command:

```bash
~ > shistGPT
[?] pick a record: C++ is a versatile high-performance programming language
 > C++ is a versatile high-performance programming language
   Communication and assistance in conversation
   Otters are social mammals found near water
```

Use `↑ / ↓` to select a conversation and hit Enter to view the selected conversation record. At this point, running `sm
oreGPT` or `lmoreGPT` will continue the conversation based on the current context.

## More Usage

### 1. Code Explanation
Run the following command:

```bash
~ > cat ./hello.cpp | saskGPT Help me explain this code
```

You will receive an explanation of the `hello.cpp` source code.

### 2. Error Analysis
Run the following command:

```bash
~ > cd aowiejfojo 2>&1 | laskGPT
```

The `stderr` output will be displayed in a text editor. After modifying the text, save and exit to ask questions.

## Configuration File

### 1. Example File
After running `shistGPT --init`, a `config.yaml` file will be created in the `~/.config/askgpt` directory of the user
who executed the command, with the following content:

```yaml
model:
    api_key: ''
    model: 'gpt-4o-mini'
    temperature: 0.8
    system_prompt:
        - make it brief if possible

net:
    proxy: 'http://192.168.4.219:10811'

record:
    max: 10

interface:
    editor: 'nano'
```

- **model** - Model-related configuration
  - **api_key** - OpenAI platform API key; the default configuration only supports the gpt-4o-mini model.
  - **model** - The model label used for conversations.
  - **temperature** - Model parameter; the higher the value, the more creative the output, the lower the value, the more
controlled the output.
  - **system_prompt** - System prompts used to constrain the conversation, multiple system prompts can be specified.

- **net** - Network connection related configuration
  - **proxy** - Proxy address used for connecting to OpenAI servers.

- **record** - History record related configuration
  - **max** - Maximum number of history records.

- **interface** - User interface related
  - **editor** - Specifies the text editor used when running `laskGPT` or `lmoreGPT`, such as `nano`, `vim`, etc.
