# Julia Generics & Multiple Dispatch — Working Notes

> Not a portfolio app — this is a learning/reference build. Julia isn't installed on this
> machine, so these are runnable-on-your-own-box notes + example files. Install Julia, then
> `julia file.jl` each section.

## The big idea: Julia is built on MULTIPLE DISPATCH
In most OOP languages, `a.foo(b)` dispatches on the *one* receiver `a`. Julia dispatches a
function on the **types of ALL arguments** at once. That single decision shapes the whole
language: generic code, zero-cost abstractions, and the "Julia solves the two-language
problem" claim all fall out of it.

```julia
# multiple dispatch: the method chosen depends on BOTH arg types
collide(a::Asteroid, b::Asteroid) = "rock vs rock"
collide(a::Asteroid, b::Ship)     = "ship takes damage"
collide(a::Ship,     b::Asteroid) = collide(b, a)
collide(a::Ship,     b::Ship)     = "both explode"
```

## Parametric types (generics)
```julia
struct Point{T}
    x::T
    y::T
end
Point(1, 2)        # Point{Int64}
Point(1.0, 2.0)    # Point{Float64}

# constrain the parameter
struct Wrapper{T<:Real}
    value::T
end
```

## Parametric methods & where-clauses
```julia
# works for ANY T, type inferred and specialized at compile time
norm2(p::Point{T}) where {T<:Real} = sqrt(p.x^2 + p.y^2)

# relate multiple type params
function combine(a::Vector{T}, b::Vector{T}) where {T}
    vcat(a, b)
end
```

## Why this is fast (the key insight)
Julia **specializes** (JIT-compiles) a fresh, monomorphic version of a generic function for
each concrete combination of argument types it's actually called with. So generic-looking
code compiles down to type-specialized machine code — no boxing, no virtual-dispatch
overhead. Generics are an abstraction you *don't pay for* at runtime.

```julia
# @code_warntype shows whether types are inferred (red = type instability = slow)
@code_warntype norm2(Point(3.0, 4.0))

# @code_native shows the actual specialized assembly
@code_native norm2(Point(3.0, 4.0))
```

## The interface pattern (Julia's "duck typing with teeth")
Julia interfaces are informal: implement the right methods and your type "just works" with
the generic ecosystem. Example — make your type iterable:

```julia
struct Squares
    count::Int
end
Base.iterate(S::Squares, state=1) = state > S.count ? nothing : (state*state, state+1)
Base.length(S::Squares) = S.count
Base.eltype(::Type{Squares}) = Int

collect(Squares(5))   # [1, 4, 9, 16, 25]  — works with the whole iteration protocol
```

## Holy traits (when you need trait-based dispatch)
```julia
abstract type Edible end
struct IsEdible <: Edible end
struct NotEdible <: Edible end

edibility(::Type{Apple}) = IsEdible()
edibility(::Type{Rock})  = NotEdible()

eat(x) = _eat(edibility(typeof(x)), x)
_eat(::IsEdible, x) = "yum"
_eat(::NotEdible, x) = "no"
```

## Pitfalls (the stuff that bites you)
- **Type instability** is the #1 perf killer. If a function's return type depends on a
  runtime value, the compiler can't specialize. Check with `@code_warntype` — chase the red.
- **Abstract field types** (`struct Foo; x::Real; end`) box the field. Use a parameter:
  `struct Foo{T<:Real}; x::T; end`.
- **`Vector{Any}`** silently kills performance. Concrete element types matter.
- **Over-constraining** signatures (`::Vector{Float64}`) loses genericity for no gain;
  prefer `::AbstractVector{<:Real}`.
- 1-based indexing and column-major arrays (like Fortran/MATLAB, unlike C/NumPy).

## Suggested exploration path
1. `dispatch.jl` — the collide example; add a 3rd type, watch methods compose.
2. `parametric.jl` — Point{T}, constrain it, break it on purpose to see the error.
3. `speed.jl` — write a type-unstable function, fix it, compare `@btime` (BenchmarkTools).
4. `iterate.jl` — implement the iteration interface on a custom type.

## Why this matters for you
Multiple dispatch is the cleanest real-world answer to the expression problem, and it's a
genuinely different mental model from the C++/Java OOP you've lived in at Adobe. Worth
internalizing even if you never ship Julia — it changes how you think about generic design.
