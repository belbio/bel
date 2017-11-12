Computed Edge Signatures
-----
See below for usage details and examples.

```
computed_signatures:

- function: list
  subject: "{{ full }}"
  relation: hasMember
  object: "{{ args }}"

- function: composite
  subject: "{{ full }}"
  relation: hasMember
  object: "{{ args }}"

- function: complex
  subject: "{{ full }}"
  relation: hasComponent
  object: "{{ args }}"

- function: degradation
  subject: "{{ full }}"
  relation: directlyDecreases
  object: "{{ args }}"

- function: activity
  subject: "{{ args[f] }}"
  relation: hasActivity
  object: "{{ p_full }}"

- function: reactants
  subject: "{{ p_full }}"
  relation: hasReactant
  object: "{{ args }}"

- function: products
  subject: "{{ p_full }}"
  relation: hasProduct
  object: "{{ args }}"

- function: variant
  subject: "{{ p_name(p_args[n]) }}"
  relation: hasVariant
  object: "{{ p_full }}"

- function: fusion
  subject: "{{ p_name(args[n]) }}"
  relation: hasFusion
  object: "{{ p_full }}"

- function: proteinModification
  subject: "{{ p_name(p_args[n]) }}"
  relation: hasModification
  object: "{{ p_full }}"
```

Using the Signatures
-----
The computed edge signatures describe a consistent way to compute an edge given a function in the AST. Anything enclosed within double quotes and double curly braces like `"{{ this }}"` denote a variable to be used. The following keyword variables are described:

- `full`: the whole given statement
- `fn_name`: the detected function
- `args` or `args[filter]`: each direct arg of `fn_name`; see below for `filter` options
- `p_name`: the parent function of `fn_name`, if available
- `p_args` or `p_args[filter]`: each direct arg of `p_name`, if available; see below for `filter` options
- `p_full`: the whole given statement as well as its parent, in the form of `p_name(full)`
- `filter`: flags used to specify certain arg types to be used in computing edges; they are:
   - `f` specifies only args that are primary functions
   - `m` specifies only args that are modifier functions
   - `n` specifies only args that are namespaces
   - `s` specifies only args that are strings

Since the signatures utilize both the function's sibling args and direct args, we need to keep track of the parent statement and its args, which is the reason we have the variables `p_name`, `p_full`, and `p_args`.

Examples of Using Variables
-----

### composite() example
Given: `composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng))`

- `full`: `composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng))`.
- `fn_name`: `composite`.
- `args`: `a(SCHEM:Lipopolysaccharide)`, `p(MGI:Ifng)`.
    - `args[f]`: `a(SCHEM:Lipopolysaccharide)`, `p(MGI:Ifng)`.
    - `args[m]`: none.
    - `args[n]`: none.
    - `args[s]`: none.
- `p_name`: no parent function.
- `p_args`: none.
- `p_full`: no parent function.

Based on the signature of `composite` above: the subject is `full`, the relation is "hasMember", and the object is `args`. Thus, the computed edges of the above example are:

- `composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng)) hasMember a(SCHEM:Lipopolysaccharide)`
- `composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng)) hasMember p(MGI:Ifng)`

Notice that there are as many edges as there are applicable args.

### fusion() example
Given: `p(fusion(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))`

- `full`: `fusion(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132")`.
- `fn_name`: `fusion`.
- `args`: `HGNC:BCR`, `"p.1_426"`, `HGNC:JAK2`, `"p.812_1132"`.
    - `args[f]`: none.
    - `args[m]`: none.
    - `args[n]`: `HGNC:BCR`, `HGNC:JAK2`.
    - `args[s]`: `"p.1_426"`, `"p.812_1132"`.
- `p_name`: `p`.
- `p_args`: `fusion(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132")`.
- `p_full`: `p(fusion(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))`.

Based on the signature of `fusion` above: the subject is `p_name(args[n])`, the relation is "hasFusion", and the object is `p_full`. Thus, the computed edges of the above example are:

- `p(HGNC:BCR) hasFusion p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))`
- `p(HGNC:JAK2) hasFusion p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))`

Notice that there are as many edges as there are applicable args (in this case, only two args are namespaces; the other two are strings).

### proteinModification() example
Given: `p(HGNC:AKT1, proteinModification(P, S, 473))`

- `full`: `proteinModification(P, S, 473)`.
- `fn_name`: `proteinModification`.
- `args`: `P`, `S`, `473`.
    - `args[f]`: none.
    - `args[m]`: none.
    - `args[n]`: none.
    - `args[s]`: `P`, `S`, `473`.
- `p_name`: `p`.
- `p_args`: `HGNC:AKT1`, `proteinModification(P, S, 473)`.
- `p_full`: `p(HGNC:AKT1, proteinModification(P, S, 473))`.

Based on the signature of `proteinModification` above: the subject is `p_name(p_args[n])`, the relation is "hasModification", and the object is `p_full`. Thus, the computed edge of the above example is:

- `p(HGNC:AKT1) hasModification p(HGNC:AKT1, proteinModification(P, S, 473))`

There is only a single computed edge because there is only one applicable namespace arg of the parent function `p()`, and that is `HGNC:AKT1`.
