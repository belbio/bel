Computed Edge Signatures
-----
See below for usage details and examples.

```
computed_signatures:

- function: list
  subject: "{{ full }}"
  relationship: hasMember
  object: "{{ parameters }}"

- function: composite
  subject: "{{ full }}"
  relationship: hasMember
  object: "{{ parameters }}"

- function: complex
  subject: "{{ full }}"
  relationship: hasComponent
  object: "{{ parameters }}"

- function: degradation
  subject: "{{ full }}"
  relationship: directlyDecreases
  object: "{{ parameters }}"

- function: activity
  subject: "{{ parameters[f] }}"
  relationship: hasActivity
  object: "{{ p_full }}"

- function: reactants
  subject: "{{ p_full }}"
  relationship: hasReactant
  object: "{{ parameters }}"

- function: products
  subject: "{{ p_full }}"
  relationship: hasProduct
  object: "{{ parameters }}"

- function: variant
  subject: "{{ p_name(p_parameters[n]) }}"
  relationship: hasVariant
  object: "{{ p_full }}"

- function: fusion
  subject: "{{ p_name(parameters[n]) }}"
  relationship: hasFusion
  object: "{{ p_full }}"

- function: proteinModification
  subject: "{{ p_name(p_parameters[n]) }}"
  relationship: hasModification
  object: "{{ p_full }}"
```

Using the Signatures
-----
The computed edge signatures describe a consistent way to compute an edge given a function in the AST. Anything enclosed within double quotes and double curly braces like `"{{ this }}"` denote a variable to be used. The following keyword variables are described:

- `full`: the whole given statement
- `fn_name`: the detected function
- `parameters` or `parameters[filter]`: each direct parameter of `fn_name`; see below for `filter` options
- `p_name`: the parent function of `fn_name`, if available
- `p_parameters` or `p_parameters[filter]`: each direct parameter of `p_name`, if available; see below for `filter` options
- `p_full`: the whole given statement as well as its parent, in the form of `p_name(full)`
- `filter`: flags used to specify certain parameter types to be used in computing edges; they are:
   - `f` specifies only parameters that are primary functions
   - `m` specifies only parameters that are modifier functions
   - `n` specifies only parameters that are namespaces
   - `s` specifies only parameters that are strings

Since the signatures utilize both the function's sibling parameters and direct parameters, we need to keep track of the parent statement and its parameters, which is the reason we have the variables `p_name`, `p_full`, and `p_parameters`.

Examples of Using Variables
-----

### composite() example
Given: `composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng))`

- `full`: `composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng))`.
- `fn_name`: `composite`.
- `parameters`: `a(SCHEM:Lipopolysaccharide)`, `p(MGI:Ifng)`.
    - `parameters[f]`: `a(SCHEM:Lipopolysaccharide)`, `p(MGI:Ifng)`.
    - `parameters[m]`: none.
    - `parameters[n]`: none.
    - `parameters[s]`: none.
- `p_name`: no parent function.
- `p_parameters`: none.
- `p_full`: no parent function.

Based on the signature of `composite` above: the subject is `full`, the relationship is "hasMember", and the object is `parameters`. Thus, the computed edges of the above example are:

- `composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng)) hasMember a(SCHEM:Lipopolysaccharide)`
- `composite(a(SCHEM:Lipopolysaccharide), p(MGI:Ifng)) hasMember p(MGI:Ifng)`

Notice that there are as many edges as there are applicable parameters.

### fusion() example
Given: `p(fusion(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))`

- `full`: `fusion(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132")`.
- `fn_name`: `fusion`.
- `parameters`: `HGNC:BCR`, `"p.1_426"`, `HGNC:JAK2`, `"p.812_1132"`.
    - `parameters[f]`: none.
    - `parameters[m]`: none.
    - `parameters[n]`: `HGNC:BCR`, `HGNC:JAK2`.
    - `parameters[s]`: `"p.1_426"`, `"p.812_1132"`.
- `p_name`: `p`.
- `p_parameters`: `fusion(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132")`.
- `p_full`: `p(fusion(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))`.

Based on the signature of `fusion` above: the subject is `p_name(parameters[n])`, the relationship is "hasFusion", and the object is `p_full`. Thus, the computed edges of the above example are:

- `p(HGNC:BCR) hasFusion p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))`
- `p(HGNC:JAK2) hasFusion p(fus(HGNC:BCR, "p.1_426", HGNC:JAK2, "p.812_1132"))`

Notice that there are as many edges as there are applicable parameters (in this case, only two parameters are namespaces; the other two are strings).

### proteinModification() example
Given: `p(HGNC:AKT1, proteinModification(P, S, 473))`

- `full`: `proteinModification(P, S, 473)`.
- `fn_name`: `proteinModification`.
- `parameters`: `P`, `S`, `473`.
    - `parameters[f]`: none.
    - `parameters[m]`: none.
    - `parameters[n]`: none.
    - `parameters[s]`: `P`, `S`, `473`.
- `p_name`: `p`.
- `p_parameters`: `HGNC:AKT1`, `proteinModification(P, S, 473)`.
- `p_full`: `p(HGNC:AKT1, proteinModification(P, S, 473))`.

Based on the signature of `proteinModification` above: the subject is `p_name(p_parameters[n])`, the relationship is "hasModification", and the object is `p_full`. Thus, the computed edge of the above example is:

- `p(HGNC:AKT1) hasModification p(HGNC:AKT1, proteinModification(P, S, 473))`

There is only a single computed edge because there is only one applicable namespace parameter of the parent function `p()`, and that is `HGNC:AKT1`.