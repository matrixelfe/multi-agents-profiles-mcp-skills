# Catálogo Completo de Skills por Perfil (Agent-Guided Installer)

> Inventario completo de **358 skills** curadas y organizadas por perfil/dominio para instalación selectiva vía **Vercel `skills` (`npx skills find` / `npx skills add`)** y resguardo en la **Bóveda Fría (`~/.agents/catalog/skills/`)**.
>
> **Regla de oro:** El perfil `core` mantiene solo **26 skills activas** (`-93%` de tokens). Todas las demás categorías se instalan en la Bóveda Fría (`0` tokens en reposo) y se activan por perfil (`switch-profile`) o bajo demanda (JIT).

---

## 0. Repositorios Oficiales Principales (Instalación Directa por Paquete)
| Paquete / Suite | Comando oficial (`npx skills add`) | Repo upstream |
|---|---|---|
| **Vercel Find-Skills (Buscador base)** | `npx skills add vercel-labs/skills --skill find-skills` | https://github.com/vercel-labs/skills |
| **Superpowers (14 skills)** | `npx skills add obra/superpowers` | https://github.com/obra/superpowers |
| **Agent Browser (Vercel Labs)** | `npx skills add vercel-labs/agent-browser` | https://github.com/vercel-labs/agent-browser |
| **Web Design Guidelines (Vercel)** | `npx skills add vercel-labs/agent-skills --skill web-design-guidelines` | https://github.com/vercel-labs/agent-skills |
| **UI/UX Pro Max** | `npx skills add nextlevelbuilder/ui-ux-pro-max-skill` | https://github.com/nextlevelbuilder/ui-ux-pro-max-skill |
| **Hallmark Design System + sloplint** | `npx skills add hallmark-design/hallmark` | https://github.com/hallmark-design/hallmark |
| **Trail of Bits Security & Engineering** | `npx skills add trailofbits/skills` | https://github.com/trailofbits/skills |
| **PMB Cross-IDE Memory** | `pmb connect` | https://github.com/pmb-memory/pmb |

---

## Índice Completo por Perfil / Categoría (358 skills)

### 1. Core & Superpowers (Activas por defecto) — `26` skills

| Skill ID | Descripción | Búsqueda / Instalación |
|---|---|---|
| `agent-browser` | Core agent-browser usage guide. Read this before running any agent-browser commands. Covers the snapshot-and-ref workflow, navigat | `npx skills find agent-browser` |
| `brainstorming` | You MUST use this before any creative work - creating features, building components, adding functionality, or modifying behavior.  | `npx skills find brainstorming` |
| `code-review-and-quality` | Conducts multi-axis code review. Use before merging any change. Use when reviewing code written by yourself, another agent, or a h | `npx skills find code-review-and-quality` |
| `code-simplification` | Simplifies code for clarity. Use when refactoring code for clarity without changing behavior. Use when code works but is harder to | `npx skills find code-simplification` |
| `context-engineering` | Optimizes agent context setup. Use when starting a new session, when agent output quality degrades, when switching between tasks,  | `npx skills find context-engineering` |
| `conventional-commits` | Apply the Conventional Commits 1.0.0 format when proposing, creating, or reviewing Git commit messages. | `npx skills find conventional-commits` |
| `dispatching-parallel-agents` | Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies | `npx skills find dispatching-parallel-agents` |
| `executing-plans` | Use when you have a written implementation plan to execute in a separate session with review checkpoints | `npx skills find executing-plans` |
| `finishing-a-development-branch` | Use when implementation is complete, all tests pass, and you need to decide how to integrate the work | `npx skills find finishing-a-development-branch` |
| `harness-engineering` | This skill should be used when designing autonomous agent harnesses: research loops, evaluation scaffolds, locked and editable sur | `npx skills find harness-engineering` |
| `modern-python` | Configures Python projects with modern tooling (uv, ruff, ty). Use when creating projects, writing standalone scripts, or migratin | `npx skills find modern-python` |
| `planning-and-task-breakdown` | Breaks work into ordered tasks. Use when you have a spec or clear requirements and need to break work into implementable tasks. Us | `npx skills find planning-and-task-breakdown` |
| `pmb-memory` | Local-first cross-agent persistent memory engine (PMB). Use this skill to query, store, and recall persistent project decisions, l | `npx skills find pmb-memory` |
| `project-changelog` | Create and maintain .agent-docs/CHANGELOG.md following Keep a Changelog. Use as soon as work starts in any repository or project,  | `npx skills find project-changelog` |
| `project-docs` | Create, update, audit and prune project documentation under .agent-docs/ plus the repo AGENTS.md. Use for documentation bootstrap  | `npx skills find project-docs` |
| `receiving-code-review` | Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically ques | `npx skills find receiving-code-review` |
| `requesting-code-review` | Use when completing tasks, implementing major features, or before merging to verify work meets requirements | `npx skills find requesting-code-review` |
| `subagent-driven-development` | Use when executing implementation plans with independent tasks in the current session | `npx skills find subagent-driven-development` |
| `systematic-debugging` | Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes | `npx skills find systematic-debugging` |
| `test-driven-development` | Drives development with tests using the red-green-refactor loop. Use when implementing any logic, fixing any bug, or changing any  | `npx skills find test-driven-development` |
| `using-agent-skills` | Discovers and invokes agent skills. Use when starting a session, or when you need to decide which skill or workflow applies to the | `npx skills find using-agent-skills` |
| `using-git-worktrees` | Use when starting feature work that needs isolation from current workspace or before executing implementation plans - ensures an i | `npx skills find using-git-worktrees` |
| `using-superpowers` | Use when starting any conversation - establishes how to find and use skills, requiring skill invocation before ANY response includ | `npx skills find using-superpowers` |
| `verification-before-completion` | Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification com | `npx skills find verification-before-completion` |
| `writing-plans` | Use when you have a spec or requirements for a multi-step task, before touching code | `npx skills find writing-plans` |
| `writing-skills` | Use when creating new skills, editing existing skills, or verifying skills work before deployment | `npx skills find writing-skills` |

### 2. Fullstack, Frontend & UI Design (perfil: web) — `99` skills

| Skill ID | Descripción | Búsqueda / Instalación |
|---|---|---|
| `animate` | Build an animation from scratch, making the decisions in the order that determines whether it feels right — should it animate at a | `npx skills find animate` |
| `animation-performance` | Keep web animations inside the frame budget — animate composite-only properties, keep motion off the main thread when the page is  | `npx skills find animation-performance` |
| `animejs-web-animation` | Design and implement web motion with Anime.js for DOM, SVG, staggered entrances, timelines, and interactive transitions. Use when  | `npx skills find animejs-web-animation` |
| `api-and-interface-design` | Guides stable API and interface design. Use when designing APIs, module boundaries, or any public interface. Use when creating RES | `npx skills find api-and-interface-design` |
| `api-connector-builder` | Build a new API connector or provider by matching the target repo's existing integration pattern exactly. Use when adding one more | `npx skills find api-connector-builder` |
| `api-design` | REST API design patterns including resource naming, status codes, pagination, filtering, error responses, versioning, and rate lim | `npx skills find api-design` |
| `apple-design` | Apple's approach to interface design and fluid, physical motion, translated for the web. Use when building or reviewing gesture-dr | `npx skills find apple-design` |
| `ask-sonner` | Guide to Sonner, the React toast library — install and wire up the Toaster, pick the right toast() call, promise and loading toast | `npx skills find ask-sonner` |
| `banner-design` | Design banners for social media, ads, website heroes, creative assets, and print. Multiple art direction options with optional gen | `npx skills find banner-design` |
| `bazel` | Bazel build system skill for C/C++ projects. Use when writing BUILD files with cc_library and cc_binary rules, registering toolcha | `npx skills find bazel` |
| `break-ui` | Try to break a piece of UI by feeding it worst-case data — long names, unbreakable emails, one-letter names, missing fields, huge  | `npx skills find break-ui` |
| `browser-qa` | Run automated post-deploy UI verification with a browser automation MCP (claude-in-chrome, Playwright, or Puppeteer): console-erro | `npx skills find browser-qa` |
| `browser-testing-with-devtools` | Tests in real browsers via Chrome DevTools MCP. Use when building or debugging anything that runs in a browser. Use when you need  | `npx skills find browser-testing-with-devtools` |
| `bus-drivers-i2c-spi` | I2C and SPI bus driver skill for Linux client drivers. Use when writing i2c_driver or spi_driver, register access over bus, DMA SP | `npx skills find bus-drivers-i2c-spi` |
| `carbon-lang` | Carbon language skill for C++ interop and toolchain. Use when evaluating Carbon syntax, bidirectional C++ interop, building carbon | `npx skills find carbon-lang` |
| `cargo-workflows` | Cargo workflow skill for Rust projects. Use when managing workspaces, feature flags, build scripts, cargo cache, incremental build | `npx skills find cargo-workflows` |
| `ci-cd-and-automation` | Automates CI/CD pipeline setup. Use when setting up or modifying build and deployment pipelines. Use when you need to automate qua | `npx skills find ci-cd-and-automation` |
| `cmake` | CMake build system skill for C/C++ projects. Use when writing or refactoring CMakeLists.txt, configuring out-of-source builds, sel | `npx skills find cmake` |
| `compiler-frontend` | Compiler frontend skill for lexing, parsing, and type checking. Use when building a lexer/parser, designing AST nodes, implementin | `npx skills find compiler-frontend` |
| `constraint-driven-development` | Establishes a project's quality bar as a written contract and stops agents quietly lowering it. Interviews the user on which dimen | `npx skills find constraint-driven-development` |
| `containers-internals` | Linux containers internals skill for namespaces, cgroups, and OCI. Use when understanding clone/unshare namespaces, cgroups v2 lim | `npx skills find containers-internals` |
| `dashboard-builder` | Build monitoring dashboards that answer real operator questions for Grafana, SigNoz, and similar platforms. Use when turning metri | `npx skills find dashboard-builder` |
| `debug-optimized-builds` | Debugging optimized builds skill for diagnosing issues in release code. Use when debugging RelWithDebInfo builds, using -Og for de | `npx skills find debug-optimized-builds` |
| `debugging-and-error-recovery` | Guides systematic root-cause debugging. Use when tests fail, builds break, something that worked yesterday broke, behavior doesn't | `npx skills find debugging-and-error-recovery` |
| `design` | Comprehensive design skill: brand identity, design tokens, UI styling, logo generation (55 styles, Gemini, Atlas Cloud, MuAPI, or  | `npx skills find design` |
| `design-system` | Token architecture, component specifications, and slide generation. Three-layer tokens (primitive→semantic→component), CSS variabl | `npx skills find design-system` |
| `device-drivers` | Linux device driver skill for kernel driver development. Use when writing platform/i2c/spi drivers, char device lifecycle, IRQ han | `npx skills find device-drivers` |
| `device-tree` | Device tree skill for Linux hardware description. Use when writing DTS/DTSI, bindings, overlays, phandles, or debugging OF platfor | `npx skills find device-tree` |
| `documentation-and-adrs` | Records decisions and documentation. Use when you need to document an architecture decision (ADR) or the reasoning behind a design | `npx skills find documentation-and-adrs` |
| `dynamic-linking` | Dynamic linking skill for Linux/ELF shared libraries. Use when debugging library loading failures, configuring RPATH vs RUNPATH, u | `npx skills find dynamic-linking` |
| `e2e-testing` | Playwright E2E testing patterns, Page Object Model, configuration, CI/CD integration, artifact management, and flaky test strategi | `npx skills find e2e-testing` |
| `ebpf` | eBPF skill for Linux observability and networking. Use when writing eBPF programs with libbpf or bpftrace, attaching kprobes/trace | `npx skills find ebpf` |
| `elf-inspection` | ELF binary inspection skill for Linux. Use when examining ELF executables or shared libraries with readelf, objdump, nm, or ldd to | `npx skills find elf-inspection` |
| `emil-design-eng` | This skill encodes Emil Kowalski's philosophy on UI polish, component design, animation decisions, and the invisible details that  | `npx skills find emil-design-eng` |
| `evaluation` | This skill should be used when building agent evaluation systems: deterministic checks, regression suites, multi-dimensional rubri | `npx skills find evaluation` |
| `find-animation-opportunities` | Search a codebase or UI for places that don't animate but should, and reject everything that shouldn't. Read-only; it proposes mot | `npx skills find find-animation-opportunities` |
| `flamegraphs` | Flamegraph generation and interpretation skill. Use when converting perf, Valgrind Callgrind, or other profiler output into SVG fl | `npx skills find flamegraphs` |
| `frontend-a11y` | Accessibility patterns for React and Next.js — semantic HTML, ARIA attributes, form labeling, keyboard navigation, focus managemen | `npx skills find frontend-a11y` |
| `frontend-design` | Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web  | `npx skills find frontend-design` |
| `frontend-design-direction` | Set an ECC-specific frontend design direction for production UI work. Use when building or improving websites, dashboards, applica | `npx skills find frontend-design-direction` |
| `frontend-patterns` | Frontend development patterns for React, Next.js, state management, performance optimization, and UI best practices. | `npx skills find frontend-patterns` |
| `frontend-ui-engineering` | Builds production-quality, accessible, responsive user-facing UIs. Use when building or modifying interfaces and pages, creating c | `npx skills find frontend-ui-engineering` |
| `gcc` | GCC compiler skill for C/C++ projects. Use when selecting optimization levels, warning flags, debug builds, LTO, sanitizer instrum | `npx skills find gcc` |
| `gh-cli` | Enforces authenticated gh CLI workflows over unauthenticated curl, WebFetch, and MCP fetch patterns. Use when working with GitHub  | `npx skills find gh-cli` |
| `hallmark` | Design skill for websites and new pages that look designed, not generated. Use when the user asks to build or design something new | `npx skills find hallmark` |
| `hare-lang` | Hare language skill for simple systems programming. Use when building with hare build/test/run, Hare stdlib, C FFI with @extern, t | `npx skills find hare-lang` |
| `heaptrack` | heaptrack memory profiler skill for Linux. Use when tracking heap allocations, finding memory leaks, measuring peak heap usage, id | `npx skills find heaptrack` |
| `hosted-agents` | This skill should be used when designing hosted or background agent infrastructure: sandboxed execution, remote coding environment | `npx skills find hosted-agents` |
| `interpreters` | Bytecode interpreter and JIT compiler skill for implementing language runtimes in C/C++. Use when designing bytecode dispatch loop | `npx skills find interpreters` |
| `io-uring` | io_uring skill for Linux async I/O. Use when building high-performance servers with liburing, multi-shot operations, provided buff | `npx skills find io-uring` |
| `jit-compilation` | JIT compilation skill for runtime code generation. Use when building LLVM ORC JIT, LLJIT, Cranelift JIT, inline caches, trampoline | `npx skills find jit-compilation` |
| `kernel-concurrency` | Kernel concurrency skill for Linux locking and synchronization. Use when choosing spinlocks vs mutexes, using RCU, seqlocks, compl | `npx skills find kernel-concurrency` |
| `kernel-debugging` | Linux kernel debugging skill for kgdb, kdb, ftrace, kprobes, and crash analysis. Use when setting up kgdb over serial, using ftrac | `npx skills find kernel-debugging` |
| `kernel-internals` | Linux kernel internals skill for scheduler, memory, and VFS subsystems. Use when analyzing CFS/EEVDF scheduling, buddy/SLUB alloca | `npx skills find kernel-internals` |
| `kernel-memory-management` | Kernel memory management skill for Linux mm subsystem. Use when using kmalloc, vmalloc, page allocator, SLUB, or debugging OOM and | `npx skills find kernel-memory-management` |
| `kernel-testing` | Linux kernel testing skill for KUnit, kselftest, syzkaller, and LTP. Use when writing KUnit tests, running kselftest harness, conf | `npx skills find kernel-testing` |
| `linux-kernel-architecture` | Linux kernel architecture skill for subsystem overview. Use when navigating kernel source, understanding boot flow, initcalls, or  | `npx skills find linux-kernel-architecture` |
| `linux-kernel-modules` | Linux kernel module skill for writing and debugging loadable kernel modules. Use when writing LKMs with Kbuild, adding module para | `npx skills find linux-kernel-modules` |
| `linux-perf` | Linux perf profiler skill for CPU performance analysis. Use when collecting sampling profiles with perf record, generating perf re | `npx skills find linux-perf` |
| `make` | GNU Make skill for C/C++ build systems. Use when writing or debugging Makefiles, understanding pattern rules and automatic depende | `npx skills find make` |
| `meson` | Meson build system skill for C/C++ projects. Use when setting up a Meson project, configuring build options, managing dependencies | `npx skills find meson` |
| `modern-cpp` | Guides C++ code toward modern idioms (C++20/23/26). Use when writing new C++ code, modernizing legacy patterns, or working on secu | `npx skills find modern-cpp` |
| `msvc-cl` | MSVC cl.exe and clang-cl skill for Windows C/C++ projects. Use when configuring Visual Studio builds, MSBuild, or clang-cl as a dr | `npx skills find msvc-cl` |
| `multi-agent-patterns` | This skill should be used when designing multi-agent systems that need context isolation, supervisor or swarm coordination, explic | `npx skills find multi-agent-patterns` |
| `nextjs-turbopack` | Next.js 16+ and Turbopack guidance — incremental Rust bundling, file-system caching, faster dev startup and HMR, Turbopack vs webp | `npx skills find nextjs-turbopack` |
| `ninja` | Ninja build system skill. Use when diagnosing Ninja build failures, understanding Ninja's role as a low-level build executor gener | `npx skills find ninja` |
| `os-dev-scratch` | OS development from scratch skill for bootloader through context switching. Use when building a minimal x86-64 OS, setting up GDT/ | `npx skills find os-dev-scratch` |
| `performance-optimization` | Optimizes application performance across frontend, backend, queries, and databases. Use when performance requirements exist, when  | `npx skills find performance-optimization` |
| `pgo` | Profile-guided optimisation skill for C/C++ with GCC and Clang. Use when squeezing maximum runtime performance after standard opti | `npx skills find pgo` |
| `pick-ui-library` | Pick the right library for a given frontend task from a curated, opinionated list — numbers, OTP inputs, charts, command menus, vi | `npx skills find pick-ui-library` |
| `platform-device-model` | Platform device model skill for Linux driver binding. Use when implementing platform_driver probe/remove, sysfs attributes, device | `npx skills find platform-device-model` |
| `prototype` | Build multiple genuinely different versions of a UI piece you describe, rendered behind a visual picker so you can flip through th | `npx skills find prototype` |
| `qemu-for-kernel-development` | QEMU kernel development skill for driver and kernel testing. Use when booting custom kernels in QEMU, Buildroot/Yocto rootfs, virt | `npx skills find qemu-for-kernel-development` |
| `react-patterns` | React 18/19 patterns including hooks discipline, server/client component boundaries, Suspense + error boundaries, form actions, da | `npx skills find react-patterns` |
| `react-performance` | React and Next.js performance optimization patterns adapted from Vercel Engineering's React Best Practices (https://github.com/ver | `npx skills find react-performance` |
| `react-testing` | React component testing with React Testing Library, Vitest/Jest, MSW for network mocking, accessibility assertions with axe, and t | `npx skills find react-testing` |
| `reproduce-regression` | Use when deploying before/after systems and building a live-system PoC for a regression candidate. | `npx skills find reproduce-regression` |
| `review-animations` | Reviews animation and motion code against a high craft bar derived from Emil Kowalski's design engineering philosophy. Default to  | `npx skills find review-animations` |
| `rust-build-times` | Rust build time optimization skill for reducing slow compilation. Use when using cargo-timings to profile builds, configuring scca | `npx skills find rust-build-times` |
| `rust-cross` | Rust cross-compilation skill. Use when building Rust binaries for a different target architecture or OS, using cross or cargo-zigb | `npx skills find rust-cross` |
| `rust-no-std` | Guide no_std Rust development for embedded and bare-metal targets. Use when writing #![no_std] crates, understanding core vs alloc | `npx skills find rust-no-std` |
| `rust-unsafe` | Rust unsafe code skill for systems programming. Use when writing or reviewing unsafe Rust, understanding what operations require u | `npx skills find rust-unsafe` |
| `rustc-basics` | Rust compiler skill for systems programming. Use when selecting RUSTFLAGS, configuring Cargo profiles, tuning release builds, read | `npx skills find rustc-basics` |
| `scrapling-official` | Scrape web pages using Scrapling with HTTP requests, stealth browsers, JavaScript rendering, browser actions, API response capture | `npx skills find scrapling-official` |
| `slides` | Create strategic HTML presentations with Chart.js, design tokens, responsive layouts, copywriting formulas, and contextual slide s | `npx skills find slides` |
| `spec-to-code-compliance` | Check code against the documentation that specifies it - which requirements hold, which the code contradicts, which are absent, an | `npx skills find spec-to-code-compliance` |
| `static-analysis` | Static analysis skill for C/C++ codebases. Use when hardening code quality, triaging noisy builds, running clang-tidy, cppcheck, o | `npx skills find static-analysis` |
| `tool-design` | This skill should be used for the tool-interface layer of an agent system specifically: writing tool descriptions agents can route | `npx skills find tool-design` |
| `ui-demo` | Record polished UI demo videos using Playwright. Use when the user asks to create a demo, walkthrough, screen recording, or tutori | `npx skills find ui-demo` |
| `ui-styling` | Create beautiful, accessible user interfaces with shadcn/ui components (built on Radix UI + Tailwind), Tailwind CSS utility-first  | `npx skills find ui-styling` |
| `vite-patterns` | Vite build tool patterns including config, plugins, HMR, env variables, proxy setup, SSR, library mode, dependency pre-bundling, a | `npx skills find vite-patterns` |
| `vue-patterns` | Vue.js 3 Composition API patterns, component architecture, reactivity best practices, Pinia state management, Vue Router navigatio | `npx skills find vue-patterns` |
| `wasm-emscripten` | WebAssembly with Emscripten skill for C/C++ to WASM compilation. Use when compiling C/C++ to WebAssembly with emcc, configuring EX | `npx skills find wasm-emscripten` |
| `wasm-wasmtime` | WebAssembly runtime skill using wasmtime. Use when running WASM modules with wasmtime CLI, working with WASI preview2, using the c | `npx skills find wasm-wasmtime` |
| `writing-char-drivers` | Character driver skill for Linux kernel char devices. Use when implementing file_operations, cdev, copy_to_user, ioctl, or mmap fo | `npx skills find writing-char-drivers` |
| `zephyr` | Zephyr RTOS skill for embedded development. Use when building Zephyr applications with west, configuring boards and targets, worki | `npx skills find zephyr` |
| `zig-build-system` | Zig build system skill for multi-file Zig projects. Use when writing or debugging build.zig files, adding executables or libraries | `npx skills find zig-build-system` |
| `zig-cross` | Zig cross-compilation skill. Use when cross-compiling Zig programs to different targets, using Zig's built-in cross-compilation fo | `npx skills find zig-cross` |
| `zig-testing` | Zig testing skill for writing and running tests. Use when using zig build test, writing comptime tests, using test filters, workin | `npx skills find zig-testing` |

### 3. Ingeniería de Sistemas, Kernel, C/C++ & Rust (perfil: windows-native) — `63` skills

| Skill ID | Descripción | Búsqueda / Instalación |
|---|---|---|
| `abi-and-calling-conventions` | ABI and calling conventions skill for cross-language boundaries. Use when explaining System V AMD64, ARM AAPCS, RISC-V psABI, stac | `npx skills find abi-and-calling-conventions` |
| `adc-dac-baremetal` | Bare-metal ADC and DAC skill. Use when configuring analog sampling, DMA-driven ADC, calibration, or DAC output on MCUs. Activates  | `npx skills find adc-dac-baremetal` |
| `af-xdp` | AF_XDP skill for high-performance XDP sockets. Use when creating AF_XDP sockets, configuring UMEM and XSK rings, XDP_REDIRECT prog | `npx skills find af-xdp` |
| `arm-sve` | ARM SVE skill for scalable vector extension programming. Use when writing SVE intrinsics, predicate registers, VLA loops with svcn | `npx skills find arm-sve` |
| `assembly-arm` | AArch64 and ARM assembly skill for reading and writing ARM assembly code. Use when reading GCC/Clang output for AArch64 or ARM Thu | `npx skills find assembly-arm` |
| `assembly-riscv` | RISC-V assembly skill for RV32/RV64 programming. Use when working with the RISC-V ISA, calling conventions (psABI), inline assembl | `npx skills find assembly-riscv` |
| `assembly-x86` | x86-64 assembly skill for reading, writing, and debugging assembly code. Use when reading GCC/Clang assembly output, writing inlin | `npx skills find assembly-x86` |
| `baremetal-startup` | Bare-metal startup skill for reset-to-main bring-up. Use when writing startup code, vector tables, .data/.bss init, stack setup, o | `npx skills find baremetal-startup` |
| `clang` | Clang/LLVM compiler skill for C/C++ projects. Use when working with clang or clang++ for diagnostics, sanitizer instrumentation, o | `npx skills find clang` |
| `code-generation-and-backends` | Code generation and backends skill for LLVM targets. Use when explaining instruction selection, DAG legalization, target lowering, | `npx skills find code-generation-and-backends` |
| `compiler-optimizations-deep` | Deep compiler optimizations skill for RA, ISel, and PGO. Use when explaining register allocation, instruction selection, LICM, vec | `npx skills find compiler-optimizations-deep` |
| `cpp-coroutines` | C++20 coroutines skill for understanding coroutine mechanics and debugging. Use when working with co_await, co_yield, co_return, i | `npx skills find cpp-coroutines` |
| `cpp-modules` | C++20 modules skill for modern C++ projects. Use when working with named modules, module partitions, header units, CMake MODULE_SO | `npx skills find cpp-modules` |
| `cpp-templates` | C++ template skill for reading template errors and optimizing compile times. Use when deciphering template error stacks, setting - | `npx skills find cpp-templates` |
| `cpu-cache-opt` | CPU cache optimization skill for C/C++ and Rust. Use when diagnosing cache misses, improving data layout for cache efficiency, usi | `npx skills find cpu-cache-opt` |
| `cuda` | CUDA C/C++ skill for NVIDIA GPU kernel programming. Use when writing CUDA kernels, managing thread/block/grid hierarchy, optimizin | `npx skills find cuda` |
| `cuda-debugging` | CUDA debugging skill for GPU program correctness. Use when debugging with cuda-gdb, running NVIDIA Compute Sanitizer memcheck/race | `npx skills find cuda-debugging` |
| `cuda-profiling` | CUDA profiling skill for NVIDIA GPU performance analysis. Use when profiling kernels with Nsight Systems or Nsight Compute, interp | `npx skills find cuda-profiling` |
| `custom-allocators` | Custom allocator skill for memory allocation strategies. Use when implementing pool/slab/arena allocators, tuning jemalloc/mimallo | `npx skills find custom-allocators` |
| `dma-baremetal` | Bare-metal DMA skill for memory-peripheral transfers. Use when configuring DMA channels, circular mode, double buffering, or DMA I | `npx skills find dma-baremetal` |
| `dpdk` | DPDK skill for userspace packet I/O. Use when initializing EAL, configuring PMD drivers, using mbuf pools and rte_ring, setting up | `npx skills find dpdk` |
| `ebpf-rust` | Rust eBPF skill using the Aya framework. Use when writing eBPF programs in Rust with aya-bpf and aya-log, defining BPF map types,  | `npx skills find ebpf-rust` |
| `embedded-rust` | Embedded Rust skill for bare-metal microcontroller development. Use when using probe-rs or cargo-embed for flashing and debugging, | `npx skills find embedded-rust` |
| `gpio-baremetal` | Bare-metal GPIO skill for pin configuration and interrupts. Use when configuring GPIO modes, alternate functions, pull resistors,  | `npx skills find gpio-baremetal` |
| `hip-rocm` | HIP and ROCm skill for AMD GPU programming. Use when writing HIP kernels with hipcc, porting CUDA code via HIPIFY, profiling with  | `npx skills find hip-rocm` |
| `hypervisor-internals` | Hardware virtualization internals skill for Intel VT-x and AMD-V. Use when studying VMCS/VMCB, EPT/NPT page tables, VMEXIT handlin | `npx skills find hypervisor-internals` |
| `interrupts-and-exceptions-baremetal` | Bare-metal interrupt and exception skill for Cortex-M NVIC. Use when writing ISRs, configuring priorities, handling HardFault, or  | `npx skills find interrupts-and-exceptions-baremetal` |
| `kernel-debugging-advanced` | Advanced kernel debugging skill for ftrace, trace-cmd, perf, kprobes, kgdb, and crash analysis. Use when tracing kernel functions, | `npx skills find kernel-debugging-advanced` |
| `linker-scripts` | Linker script skill for embedded bare-metal targets. Use when writing or modifying GNU ld linker scripts, placing code and data in | `npx skills find linker-scripts` |
| `linkers-lto` | Linker and Link-Time Optimisation (LTO) skill. Use when configuring GNU ld, gold, or lld linker flags, diagnosing link-order issue | `npx skills find linkers-lto` |
| `llvm` | LLVM IR and pass pipeline skill. Use when working directly with LLVM Intermediate Representation (IR), running opt passes, generat | `npx skills find llvm` |
| `llvm-ir-and-passes` | LLVM IR and passes skill for reading compiler IR. Use when analyzing LLVM IR, understanding SSA, pass pipeline order, or running o | `npx skills find llvm-ir-and-passes` |
| `llvm-passes` | LLVM passes skill for writing compiler optimizations. Use when writing FunctionPass or ModulePass, registering PassPlugins, runnin | `npx skills find llvm-passes` |
| `low-power-embedded` | Low-power embedded skill for sleep modes and energy optimization. Use when configuring MCU sleep/stop/standby, peripheral clock ga | `npx skills find low-power-embedded` |
| `memory-model` | C++ and Rust memory model skill for concurrent programming. Use when understanding memory ordering, writing lock-free data structu | `npx skills find memory-model` |
| `mlir` | MLIR skill for multi-level intermediate representation. Use when writing custom dialects, defining ops with ODS, writing lowering  | `npx skills find mlir` |
| `observability-and-instrumentation` | Instruments code so production behavior is visible and diagnosable. Use when adding logging, metrics, tracing, or alerting. Use wh | `npx skills find observability-and-instrumentation` |
| `openmp` | OpenMP skill for shared-memory parallel programming. Use when writing parallel for loops, reductions, task parallelism, SIMD direc | `npx skills find openmp` |
| `openocd-jtag` | OpenOCD skill for embedded hardware debugging. Use when configuring OpenOCD for JTAG or SWD targets, flashing firmware, connecting | `npx skills find openocd-jtag` |
| `peripherals-from-datasheet` | Peripheral driver methodology skill from MCU reference manuals. Use when reading register maps, timing diagrams, and writing drive | `npx skills find peripherals-from-datasheet` |
| `protocol-analysis` | Protocol analysis skill for serial bus debugging. Use when decoding I2C/SPI/UART with logic analyzer concepts, sigrok/PulseView, o | `npx skills find protocol-analysis` |
| `qemu-embedded-simulation` | QEMU embedded simulation skill for bare-metal MCU testing. Use when running ARM/RISC-V firmware in QEMU, selecting machine models, | `npx skills find qemu-embedded-simulation` |
| `qemu-kvm` | QEMU/KVM skill for virtualization and kernel development. Use when running qemu-system-x86_64 with KVM, configuring virtio devices | `npx skills find qemu-kvm` |
| `rdma-verbs` | RDMA verbs skill for InfiniBand and RoCE programming. Use when using libibverbs API, creating queue pairs, RDMA read/write operati | `npx skills find rdma-verbs` |
| `riscv-privileged` | RISC-V privileged architecture skill for M/S/U modes and traps. Use when handling CSRs, trap handlers, PLIC/CLINT interrupts, Open | `npx skills find riscv-privileged` |
| `rust-anything` | Port TypeScript/JavaScript, Python, C, Go, Ruby or Java to Rust with the rust-anything CLI or MCP tools, from one hot function up  | `npx skills find rust-anything` |
| `rust-async-internals` | Rust async internals skill for understanding and debugging async Rust. Use when understanding the Future trait and poll model, Pin | `npx skills find rust-async-internals` |
| `rust-debugging` | Rust debugging skill for systems programming. Use when debugging Rust binaries with GDB or LLDB, enabling Rust pretty-printers, in | `npx skills find rust-debugging` |
| `rust-profiling` | Rust profiling skill for performance analysis. Use when generating flamegraphs from Rust binaries, measuring monomorphization bloa | `npx skills find rust-profiling` |
| `rust-sanitizers-miri` | Rust sanitizers and Miri skill for memory safety validation. Use when running AddressSanitizer or ThreadSanitizer on Rust code, in | `npx skills find rust-sanitizers-miri` |
| `self-improvement-loops` | This skill should be used when the harness, scaffold, workflow, or optimizer itself is the optimization target: recursive self-imp | `npx skills find self-improvement-loops` |
| `self-managed-context` | This skill should be used when a model gets read-write control over its own live context window instead of a harness-scheduled com | `npx skills find self-managed-context` |
| `simd-intrinsics` | SIMD intrinsics skill for x86 (SSE/AVX) and ARM (NEON) vectorization. Use when reading auto-vectorization reports, writing SSE2/AV | `npx skills find simd-intrinsics` |
| `spi-i2c-baremetal` | Bare-metal SPI and I2C skill for serial peripheral buses. Use when implementing master-mode transfers, register read/write protoco | `npx skills find spi-i2c-baremetal` |
| `stm32-baremetal` | STM32 bare-metal skill for CMSIS-only MCU projects. Use when scaffolding STM32 firmware without HAL, configuring clocks/RCC, using | `npx skills find stm32-baremetal` |
| `timers-pwm-baremetal` | Bare-metal timer and PWM skill. Use when configuring general-purpose timers for PWM, input capture, or periodic ticks without RTOS | `npx skills find timers-pwm-baremetal` |
| `triton-lang` | Triton language skill for Python GPU kernel authoring. Use when writing Triton kernels with @triton.jit, tl.load/store, masking, a | `npx skills find triton-lang` |
| `uart-serial-baremetal` | Bare-metal UART skill for serial console and debug. Use when configuring baud rate, polling or IRQ-driven TX/RX, or integrating DM | `npx skills find uart-serial-baremetal` |
| `verilog-basics-for-lowlevel` | Verilog basics skill for firmware and kernel engineers. Use when reading RTL to understand hardware behavior, reset/clock domains, | `npx skills find verilog-basics-for-lowlevel` |
| `zig-cinterop` | Zig C interoperability skill. Use when calling C from Zig, calling Zig from C, using @cImport and @cInclude, running translate-c o | `npx skills find zig-cinterop` |
| `zig-compiler` | Zig compiler skill for systems programming. Use when compiling Zig programs, selecting optimization modes, using zig cc as a C com | `npx skills find zig-compiler` |
| `zig-comptime` | Zig comptime skill for compile-time evaluation and metaprogramming. Use when using comptime parameters, comptime types, generics v | `npx skills find zig-comptime` |
| `zig-debugging` | Zig debugging skill. Use when debugging Zig programs with GDB or LLDB, interpreting Zig runtime panics, using std.debug.print for  | `npx skills find zig-debugging` |

### 4. GameDev & 3D (perfil: gamedev) — `30` skills

| Skill ID | Descripción | Búsqueda / Instalación |
|---|---|---|
| `apple-silicon` | Apple Silicon skill for M-series development and profiling. Use when leveraging unified memory, Metal Performance Shaders, Instrum | `npx skills find apple-silicon` |
| `build-acceleration` | Build acceleration skill for C/C++ projects. Use when reducing compilation times with ccache, sccache, distcc, unity builds, preco | `npx skills find build-acceleration` |
| `gamedev-animation` | Skill especializada | `npx skills find gamedev-animation` |
| `gamedev-art-direction` | Skill especializada | `npx skills find gamedev-art-direction` |
| `gamedev-audio-wire` | Skill especializada | `npx skills find gamedev-audio-wire` |
| `gamedev-blender-headless` | Skill especializada | `npx skills find gamedev-blender-headless` |
| `gamedev-boss-encounter` | Skill especializada | `npx skills find gamedev-boss-encounter` |
| `gamedev-camera` | Skill especializada | `npx skills find gamedev-camera` |
| `gamedev-concept-judge` | Skill especializada | `npx skills find gamedev-concept-judge` |
| `gamedev-concept-lab` | Skill especializada | `npx skills find gamedev-concept-lab` |
| `gamedev-debugging` | Skill especializada | `npx skills find gamedev-debugging` |
| `gamedev-foliage` | Skill especializada | `npx skills find gamedev-foliage` |
| `gamedev-game-testing` | Skill especializada | `npx skills find gamedev-game-testing` |
| `gamedev-gameplay-systems` | Skill especializada | `npx skills find gamedev-gameplay-systems` |
| `gamedev-godot-pipeline` | Skill especializada | `npx skills find gamedev-godot-pipeline` |
| `gamedev-godot-visual-polish` | Skill especializada | `npx skills find gamedev-godot-visual-polish` |
| `gamedev-lighting` | Skill especializada | `npx skills find gamedev-lighting` |
| `gamedev-locomotion` | Skill especializada | `npx skills find gamedev-locomotion` |
| `gamedev-modular-kit` | Skill especializada | `npx skills find gamedev-modular-kit` |
| `gamedev-orchestrator` | Skill especializada | `npx skills find gamedev-orchestrator` |
| `gamedev-performance` | Skill especializada | `npx skills find gamedev-performance` |
| `gamedev-procedural-modeling` | Skill especializada | `npx skills find gamedev-procedural-modeling` |
| `gamedev-reference-reconstruction` | Skill especializada | `npx skills find gamedev-reference-reconstruction` |
| `gamedev-texture-authoring` | Skill especializada | `npx skills find gamedev-texture-authoring` |
| `gamedev-unity-pipeline` | Skill especializada | `npx skills find gamedev-unity-pipeline` |
| `gamedev-verification` | Skill especializada | `npx skills find gamedev-verification` |
| `gamedev-vfx-impact` | Skill especializada | `npx skills find gamedev-vfx-impact` |
| `gamedev-visual-artifacts` | Skill especializada | `npx skills find gamedev-visual-artifacts` |
| `gamedev-visual-iteration` | Skill especializada | `npx skills find gamedev-visual-iteration` |
| `gamedev-world-from-data` | Skill especializada | `npx skills find gamedev-world-from-data` |

### 5. Mobile — Android / iOS / Expo (perfil: android) — `21` skills

| Skill ID | Descripción | Búsqueda / Instalación |
|---|---|---|
| `accessibility` | Design, implement, and audit accessible UI to WCAG 2.2 Level AA across Web, iOS, and Android — semantic ARIA roles and labels, acc | `npx skills find accessibility` |
| `android` | Use when working with Android devices via ADB - connecting devices, running shell commands, installing apps, debugging, taking scr | `npx skills find android` |
| `android-build` | Use when building Android apps (Gradle CLI) or ROMs (AOSP, LineageOS). Triggers on "gradle build", "assemble", "AOSP", "LineageOS" | `npx skills find android-build` |
| `android-fastboot` | Use for fastboot operations, flashing partitions, bootloader unlocking, recovery mode, or partition management. Triggers on "fastb | `npx skills find android-fastboot` |
| `animate-expo` | Build animations in React Native and Expo, making the decisions in the order that determines whether they feel right — should it a | `npx skills find animate-expo` |
| `eas-app-stores` | Build and submit iOS and Android apps with EAS to TestFlight, the App Store, or Google Play. Supports Expo and other React Native  | `npx skills find eas-app-stores` |
| `eas-update` | Configure and use EAS Update for over-the-air JavaScript and asset updates with expo-updates and EAS CLI. Use when setting up OTA  | `npx skills find eas-update` |
| `eas-workflows` | Helps understand and write EAS workflow YAML files for Expo projects. Use this skill when the user asks about CI/CD or workflows i | `npx skills find eas-workflows` |
| `expo-design-system` | Create or extend an Expo app's theme, design tokens, and reusable component conventions. Use for inconsistent styling, generic or  | `npx skills find expo-design-system` |
| `expo-native-ui` | Build beautiful, native-feeling Expo screens. Covers Apple HIG styling, semantic colors, native controls, SF Symbols, media, visua | `npx skills find expo-native-ui` |
| `expo-router` | Navigation and routing for Expo Router. Covers file-based routes, groups and dynamic routes, folder organization, Link with previe | `npx skills find expo-router` |
| `expo-ui` | Build native UI with the @expo/ui package: real SwiftUI on iOS and Jetpack Compose on Android. Default to @expo/ui for sheets (Bot | `npx skills find expo-ui` |
| `lineageos` | Use when working with LineageOS custom ROM development, including syncing sources, building, device trees, repopick, Gerrit contri | `npx skills find lineageos` |
| `liquid-glass-design` | iOS 26 Liquid Glass design system — dynamic glass material with blur, reflection, and interactive morphing for SwiftUI, UIKit, and | `npx skills find liquid-glass-design` |
| `lldb` | LLDB debugger skill for C/C++/Swift/Objective-C programs. Use when debugging with LLDB on macOS, FreeBSD, or Linux-clang environme | `npx skills find lldb` |
| `mobile-native` | Make a web app feel native on a phone — the small CSS and meta-tag fixes that separate "a website in a browser" from something tha | `npx skills find mobile-native` |
| `rust-ffi` | Rust FFI skill for C interoperability. Use when calling C libraries from Rust, generating Rust bindings with bindgen, exporting Ru | `npx skills find rust-ffi` |
| `ui-to-vue` | Use when the user has UI screenshots or design exports that need batch conversion into Vue 3 components, especially with Vant, Ele | `npx skills find ui-to-vue` |
| `ui-ux-pro-max` | UI/UX design intelligence for web, mobile, and desktop. This skill should be used when designing, building, reviewing, or fixing i | `npx skills find ui-ux-pro-max` |
| `vercel-react-native-skills` | Skill especializada | `npx skills find vercel-react-native-skills` |
| `write-swift` | How to write modern Swift well — modeling with value types, Swift 6 data-race safety and approachable concurrency (@concurrent, ma | `npx skills find write-swift` |

### 6. Seguridad, Auditoría & Reverse Engineering (perfil: reverse / security) — `37` skills

| Skill ID | Descripción | Búsqueda / Instalación |
|---|---|---|
| `animation-vocabulary` | Reverse-lookup glossary that turns a vague description of a web animation or motion effect into its exact term ("the bouncy thing  | `npx skills find animation-vocabulary` |
| `audit-augmentation` | Skill especializada | `npx skills find audit-augmentation` |
| `binary-hardening` | Binary hardening skill for security-hardened C/C++ builds. Use when enabling RELRO, PIE, stack canaries, FORTIFY_SOURCE, CFI sanit | `npx skills find binary-hardening` |
| `branch-prediction-and-speculation` | Branch prediction and speculation skill for CPU security and performance. Use when explaining branch predictors, mispredict penalt | `npx skills find branch-prediction-and-speculation` |
| `codeql` | Skill especializada | `npx skills find codeql` |
| `craft-anything` | Investigate how shipped software works (programs, apps, packages, firmware, web bundles) with evidence-backed answers through the  | `npx skills find craft-anything` |
| `crypto-protocol-diagram` | Extracts protocol message flow from source code, RFCs, academic papers, pseudocode, informal prose, ProVerif (.pv), or Tamarin (.s | `npx skills find crypto-protocol-diagram` |
| `differential-review` | Performs security-focused differential review of code changes. Adapts analysis depth to codebase size, uses git blame for context, | `npx skills find differential-review` |
| `fuzzing` | Fuzzing skill for automated input-driven bug finding in C/C++. Use when setting up libFuzzer or AFL++ fuzz targets, defining fuzz  | `npx skills find fuzzing` |
| `graphify` | any input (code, docs, papers, images) - knowledge graph - clustered communities - HTML + JSON + audit report | `npx skills find graphify` |
| `improve-animations` | Survey a codebase's animation and motion code as a senior motion advisor, then produce a prioritized audit and self-contained impl | `npx skills find improve-animations` |
| `kernel-security` | Linux kernel security skill for LSM, hardening, and exploit mitigations. Use when writing SELinux/AppArmor policies, seccomp-bpf f | `npx skills find kernel-security` |
| `mermaid-to-proverif` | Translates Mermaid sequenceDiagrams describing cryptographic protocols into ProVerif formal verification models (.pv files). Use w | `npx skills find mermaid-to-proverif` |
| `prove-patch` | Use when a local security patch commit needs independent scoped and three-arm proof. | `npx skills find prove-patch` |
| `rea-analysis-optimization` | Optimize REA providers and shared analysis workflows for agent context, latency, CPU, and memory while preserving correctness and  | `npx skills find rea-analysis-optimization` |
| `rea-changelog-update` | Prepare or rewrite REA release changelogs and GitHub release notes from pinned Git history, with verified contributor thanks and R | `npx skills find rea-changelog-update` |
| `rea-ci-tests-audit` | Audit REA CI and test suites for correctness, fixture drift, false passes, and measured performance; use for suite or workflow inv | `npx skills find rea-ci-tests-audit` |
| `rea-tool-design` | Audit, investigate, design, or change REA investigation tools, CLI/MCP contracts, provider capabilities, and Evidence semantics. | `npx skills find rea-tool-design` |
| `reverse-engineer-anything` | Reverse engineer native, managed, Electron/JavaScript, packaged, firmware, and browser targets with REA, and build agent environme | `npx skills find reverse-engineer-anything` |
| `reverse-engineering` | Reverse engineering skill for binary analysis. Use when decompiling with Ghidra, analyzing with radare2, scripting RE tools, triag | `npx skills find reverse-engineering` |
| `rust-review` | Performs comprehensive Rust security review for safe/unsafe boundary issues, memory safety in unsafe blocks, concurrency hazards,  | `npx skills find rust-review` |
| `rust-security` | Rust security skill for supply chain safety and memory-safe development. Use when auditing dependencies with cargo-audit, enforcin | `npx skills find rust-security` |
| `sarif-parsing` | Skill especializada | `npx skills find sarif-parsing` |
| `security-and-hardening` | Hardens code against vulnerabilities. Use when auditing an input handler for vulnerabilities, when handling user input, authentica | `npx skills find security-and-hardening` |
| `security-bounty-hunter` | Hunt for exploitable, bounty-worthy security issues in repositories. Focuses on remotely reachable vulnerabilities that qualify fo | `npx skills find security-bounty-hunter` |
| `security-review` | Security review checklist and patterns for adding authentication, handling user input, managing secrets, creating API endpoints, o | `npx skills find security-review` |
| `security-scan` | Scan your Claude Code configuration (.claude/ directory) for security vulnerabilities, misconfigurations, and injection risks usin | `npx skills find security-scan` |
| `semgrep` | Skill especializada | `npx skills find semgrep` |
| `semgrep-rule-creator` | Creates custom Semgrep rules for detecting security vulnerabilities, bug patterns, and code patterns. Use when writing Semgrep rul | `npx skills find semgrep-rule-creator` |
| `taint-trace` | Improves taint-analysis coverage and precision by using Trailmark graphs to repair native source, sink, sanitizer, propagation, an | `npx skills find taint-trace` |
| `trailmark` | Builds and queries multi-language source and binary code graphs for security analysis. Includes pre-analysis passes for blast radi | `npx skills find trailmark` |
| `trailmark-finding-triage` | Performs graph-assisted triage of a single security finding, SARIF result, weAudit annotation, suspicious function, or report exce | `npx skills find trailmark-finding-triage` |
| `trailmark-structural` | Runs full Trailmark structural analysis by building a graph, running `preanalysis()`, and reporting hotspots, taint, blast radius, | `npx skills find trailmark-structural` |
| `trailmark-variant-neighborhood` | Expands one confirmed or suspected vulnerability into a Trailmark graph neighborhood of variant candidates by finding sibling func | `npx skills find trailmark-variant-neighborhood` |
| `vector-forge` | Mutation-driven test vector generation. Finds implementations of a cryptographic algorithm or protocol, runs mutation testing to i | `npx skills find vector-forge` |
| `web-design-guidelines` | Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", " | `npx skills find web-design-guidelines` |
| `web-perimeter-owasp-2025-audit` | Passive, non-destructive web perimeter security auditing mapped to OWASP Top 10:2025 surface leads, CDN Unkeyed Header Web Cache P | `npx skills find web-perimeter-owasp-2025-audit` |

### 7. Testing, QA, Performance & DevOps — `21` skills

| Skill ID | Descripción | Búsqueda / Instalación |
|---|---|---|
| `adjudicate-regression` | Use when deciding whether source and live reproduction evidence establish a new regression or an exclusion. | `npx skills find adjudicate-regression` |
| `commit-skill` | Skill especializada | `npx skills find commit-skill` |
| `concurrency-debugging` | Concurrency debugging skill for diagnosing data races and deadlocks. Use when reading TSan race reports, debugging deadlocks with  | `npx skills find concurrency-debugging` |
| `ctx-upgrade` | Update context-mode to the latest release. | `npx skills find ctx-upgrade` |
| `dwarf-debug-format` | DWARF debug format skill for understanding debug information. Use when inspecting DWARF sections with dwarfdump, working with spli | `npx skills find dwarf-debug-format` |
| `gdb` | GDB debugger skill for C/C++ programs. Use when starting a GDB session, setting breakpoints, stepping through code, inspecting var | `npx skills find gdb` |
| `genotoxic` | Graph-informed mutation testing triage. Parses codebases with Trailmark, runs mutation testing and necessist, then uses survived m | `npx skills find genotoxic` |
| `git-cleanup` | Safely analyzes and cleans up local git branches and worktrees, categorizing them as merged, squash-merged, superseded, or active  | `npx skills find git-cleanup` |
| `git-workflow-and-versioning` | Structures git workflow practices. Use when making any code change. Use when committing, branching, resolving conflicts, splitting | `npx skills find git-workflow-and-versioning` |
| `hardware-counters` | Hardware performance counter skill for low-level CPU analysis. Use when collecting PMU events with perf stat, using the PAPI libra | `npx skills find hardware-counters` |
| `hunt-regressions` | Use when discovering possible regressions from a pinned change and its callers before reproduction. | `npx skills find hunt-regressions` |
| `implement-patch` | Use when a confirmed local bug needs an invariant-level fix, variant search, tests, and one local commit. | `npx skills find implement-patch` |
| `patching-bugs` | Use when a known bug or falsifiable bug hypothesis in a local codebase needs a patch commit and reviewable proof report. | `npx skills find patching-bugs` |
| `prepare-regression` | Use when pinning before/after sources and collecting PR or commit context for a regression investigation. | `npx skills find prepare-regression` |
| `regression-hunt` | Use when investigating regressions in PRs or commits, coordinating a regression campaign, or resuming saved progress. | `npx skills find regression-hunt` |
| `replay-regression` | Use when independently verifying a supplied PoC against fresh live before/after deployments. | `npx skills find replay-regression` |
| `report-regressions` | Use when assembling or refreshing an evidence-linked regression report from saved campaign decisions. | `npx skills find report-regressions` |
| `second-opinion` | Gets independent code reviews from Codex or Antigravity for uncommitted changes, branch diffs, and commits. Use when the user requ | `npx skills find second-opinion` |
| `shipping-and-launch` | Prepares production launches. Use when preparing to deploy to production, or when asking what needs to be in place before shipping | `npx skills find shipping-and-launch` |
| `superpowers-test-driven-development` | Use when implementing any feature or bugfix, before writing implementation code | `npx skills find superpowers-test-driven-development` |
| `trailmark-review-gate` | Runs a Trailmark structural review gate over a branch, pull request, fix commit, release diff, or git ref range to detect new entr | `npx skills find trailmark-review-gate` |

### 8. Agentes, Contexto, Memoria & Evaluación — `41` skills

| Skill ID | Descripción | Búsqueda / Instalación |
|---|---|---|
| `advanced-evaluation` | This skill should be used for advanced LLM evaluation: LLM-as-judge systems, direct scoring, pairwise comparison, rubric calibrati | `npx skills find advanced-evaluation` |
| `bdi-mental-states` | This skill should be used when modeling agent mental states with BDI concepts: beliefs, desires, intentions, RDF-to-belief transfo | `npx skills find bdi-mental-states` |
| `binutils` | GNU binutils skill for binary manipulation and analysis. Use when using ar for static libraries, strip or objcopy for binary proce | `npx skills find binutils` |
| `bootloaders-embedded` | Embedded bootloader skill for firmware update and app handoff. Use when writing a custom bootloader, jumping to application code,  | `npx skills find bootloaders-embedded` |
| `code-improver` | Runs an autonomous review-and-fix improvement loop over any code target — a skill, plugin, module, or directory — using a reviewer | `npx skills find code-improver` |
| `code-mode` | Code-Mode execution engine (UTCP). Allows AI agents to execute multi-step tool workflows, external APIs, and MCP tools through san | `npx skills find code-mode` |
| `conan-vcpkg` | C/C++ package manager skill covering Conan and vcpkg. Use when adding third-party library dependencies to C/C++ projects, managing | `npx skills find conan-vcpkg` |
| `context-compression` | This skill should be used when long-running agent sessions need context compression, structured summarization, compaction, token-p | `npx skills find context-compression` |
| `context-degradation` | This skill should be used for diagnosing and mitigating context degradation: lost-in-middle failures, context poisoning, context c | `npx skills find context-degradation` |
| `context-fundamentals` | This skill should be used to explain or reason about the foundational concepts of context engineering: what context is, the anatom | `npx skills find context-fundamentals` |
| `context-optimization` | This skill should be used for improving context efficiency: context budgeting, observation masking, prefix or KV-cache strategy, p | `npx skills find context-optimization` |
| `core-dumps` | Core dump analysis skill for production crash triage. Use when loading core files in GDB or LLDB, enabling core dump generation on | `npx skills find core-dumps` |
| `cpu-pipelines-and-hazards` | CPU pipeline skill for hazards, forwarding, and stalls. Use when explaining pipeline stages, data/control hazards, forwarding path | `npx skills find cpu-pipelines-and-hazards` |
| `cross-gcc` | Cross-compilation with GCC skill for embedded and multi-architecture targets. Use when setting up cross-gcc toolchains, configurin | `npx skills find cross-gcc` |
| `ctx-doctor` | Check that context-mode is installed and working, as a table. | `npx skills find ctx-doctor` |
| `ctx-stats` | Show how much context context-mode saved, as a detailed report. | `npx skills find ctx-stats` |
| `datasheet-and-refmanual-reading` | Datasheet and reference manual reading skill for embedded engineers. Use when extracting pinouts, electrical limits, register maps | `npx skills find datasheet-and-refmanual-reading` |
| `doubt-driven-development` | Subjects every non-trivial decision to a fresh-context adversarial review before it stands. Use when you want every assumption cro | `npx skills find doubt-driven-development` |
| `filesystem-context` | This skill should be used when agent work needs file-backed context: durable scratchpads, tool-output offloading, just-in-time dis | `npx skills find filesystem-context` |
| `find-skills` | Helps users discover and install agent skills when they ask questions like "how do I do X", "find a skill for X", "is there a skil | `npx skills find find-skills` |
| `freertos` | FreeRTOS skill for embedded RTOS development. Use when creating tasks, managing priorities, using queues and mutexes, detecting st | `npx skills find freertos` |
| `gpu-memory-model` | GPU memory model skill for SIMT execution and memory hierarchy. Use when analyzing warp divergence, memory coalescing, shared memo | `npx skills find gpu-memory-model` |
| `headroom` | Use when a Python or TypeScript app sends large tool outputs, logs, JSON, search results or long chat history to an LLM and the ta | `npx skills find headroom` |
| `include-what-you-use` | Include What You Use (IWYU) skill for optimizing C/C++ header includes. Use when reducing compilation cascades, interpreting IWYU  | `npx skills find include-what-you-use` |
| `intel-vtune-amd-uprof` | Intel VTune and AMD uProf profiling skill for microarchitecture analysis. Use when analyzing hotspots, microarchitecture bottlenec | `npx skills find intel-vtune-amd-uprof` |
| `latent-briefing` | This skill should be used when the user asks to \"share memory between agents\", \"KV cache compaction for multi-agent\", \"orches | `npx skills find latent-briefing` |
| `long-horizon-prompting` | This skill should be used when writing, enhancing, or evaluating the launch prompt for a long-running autonomous agent or a parall | `npx skills find long-horizon-prompting` |
| `memory-hierarchy-and-caches` | Memory hierarchy skill for caches, coherence, and locality. Use when explaining cache levels, associativity, false sharing, prefet | `npx skills find memory-hierarchy-and-caches` |
| `memory-systems` | This skill should be used for persistent semantic memory in agent systems: cross-session knowledge retention, entity tracking, tem | `npx skills find memory-systems` |
| `mmio-and-bit-manipulation` | MMIO and register access skill for bare-metal firmware. Use when accessing memory-mapped peripherals with volatile, bit masks, RMW | `npx skills find mmio-and-bit-manipulation` |
| `mpi` | MPI skill for distributed-memory parallel programming. Use when writing MPI_Send/Recv programs, collective operations, non-blockin | `npx skills find mpi` |
| `numa-programming` | NUMA programming skill for multi-socket memory locality. Use when detecting NUMA topology, binding processes with numactl, using l | `npx skills find numa-programming` |
| `project-development` | This skill should be used for project-level decisions about LLM-powered systems: whether an LLM is the right primitive for the tas | `npx skills find project-development` |
| `resource-optimization-lowend` | Resource optimization skill for constrained embedded targets. Use when reducing flash/RAM usage, analyzing stack depth, reading li | `npx skills find resource-optimization-lowend` |
| `sanitizers` | Compiler sanitizer skill for runtime bug detection in C/C++. Use when enabling and interpreting AddressSanitizer (ASan), Undefined | `npx skills find sanitizers` |
| `skill-improver` | Runs an autonomous review-and-fix improvement loop over a Claude Code skill until a review comes back clean, with a cross-round fi | `npx skills find skill-improver` |
| `slicing-code-context` | Selects bounded, graph-informed source slices with Trailmark and delegates focused code analysis or patch-proposal work to a small | `npx skills find slicing-code-context` |
| `source-driven-development` | Grounds every implementation decision in official documentation. Use when you want to verify an approach against the official docs | `npx skills find source-driven-development` |
| `strace-ltrace` | strace and ltrace skill for system call and library call tracing. Use when a binary behaves incorrectly without crashing, diagnosi | `npx skills find strace-ltrace` |
| `valgrind` | Valgrind profiler skill for memory error detection and cache profiling. Use when running Memcheck to find heap corruption, use-aft | `npx skills find valgrind` |
| `virtual-memory-paging-and-tlb` | Virtual memory skill for paging, page tables, and TLB. Use when explaining page faults, multi-level page tables, TLB behavior, or  | `npx skills find virtual-memory-paging-and-tlb` |

### 9. Utilidades Generales & Productividad — `20` skills

| Skill ID | Descripción | Búsqueda / Instalación |
|---|---|---|
| `.system` | Skill especializada | `npx skills find .system` |
| `brand` | Brand voice, visual identity, messaging frameworks, asset management, brand consistency. Activate for branded content, tone of voi | `npx skills find brand` |
| `continuous-learning-v2` | Instinct-based learning system that observes sessions via hooks, creates atomic instincts with confidence scoring, and evolves the | `npx skills find continuous-learning-v2` |
| `deprecation-and-migration` | Manages deprecation and migration. Use when removing old systems, APIs, or features. Use when migrating users from one implementat | `npx skills find deprecation-and-migration` |
| `diagramming-code` | Skill especializada | `npx skills find diagramming-code` |
| `fastapi-patterns` | FastAPI best practices covering project structure, Pydantic v2 schemas, dependency injection, async handlers, authentication, auth | `npx skills find fastapi-patterns` |
| `graph-evolution` | Skill especializada | `npx skills find graph-evolution` |
| `idea-refine` | Refines raw ideas into sharp, actionable concepts through structured divergent and convergent thinking. Use when an idea is still  | `npx skills find idea-refine` |
| `incremental-implementation` | Delivers changes incrementally in thin, verifiable slices. Use when implementing any feature or change that touches more than one  | `npx skills find incremental-implementation` |
| `interview-me` | Extracts what the user actually wants instead of what they think they should want. Achieves this through one-question-at-a-time in | `npx skills find interview-me` |
| `nestjs-patterns` | NestJS architecture patterns for modules, controllers, providers, DTO validation, guards, interceptors, config, and production-gra | `npx skills find nestjs-patterns` |
| `pr-improver` | Runs an autonomous review-and-fix improvement loop over the current branch's changes until a PR review comes back clean, scoped me | `npx skills find pr-improver` |
| `reproduce-bug` | Use when a named runtime or compiler bug in a local repository needs independent reproduction. | `npx skills find reproduce-bug` |
| `rtk-tdd` | Skill especializada | `npx skills find rtk-tdd` |
| `rtk-triage` | Skill especializada | `npx skills find rtk-triage` |
| `spec-driven-development` | Creates specs before coding. Use when starting a new project, feature, or significant change and no specification exists yet. Use  | `npx skills find spec-driven-development` |
| `trailmark-summary` | Runs a Trailmark summary analysis on a codebase. Returns auto-detected languages, entry point count, and dependency list. Use when | `npx skills find trailmark-summary` |
| `typescript-patterns` | TypeScript patterns for strict, type-safe, maintainable code in modern TypeScript and JavaScript applications. Covers strict compi | `npx skills find typescript-patterns` |
| `validate-bug` | Use when a bug PoC package needs an independent rerun and judgment before patching. | `npx skills find validate-bug` |
| `variant-analysis` | Hunts for the other instances of a bug already found — the variants of one root cause across a codebase. Use immediately after a v | `npx skills find variant-analysis` |

---

## Protocolo de Inspección y Auto-Reparación Post-Instalación
Al instalar cualquier skill desde este catálogo (vía agente o desde el Instalador Web de `agent-tooling ui`), el sistema verifica y corrige automáticamente:
1. **Consolidación en Bóveda Fría:** mueve carpetas sueltas hacia `~/.agents/catalog/skills/<id>` y crea NTFS Junction en `~/.agents/skills/<id>` solo si pertenece al perfil activo.
2. **Validación y reparación de `SKILL.md`:** recupera `SKILL.md` anidados y repara frontmatter YAML (`name`, `description`) si falta.
3. **Detección de Hooks y Scripts:** inspecciona `hooks/`, `hooks.json` y `scripts/` (`*.ps1`, `*.mjs`, `*.py`, `*.sh`) e informa si requieren registro en el IDE sin sobrescribir hooks existentes.
