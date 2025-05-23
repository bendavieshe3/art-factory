# Expando Script

The expando script is a Draw Things script which takes the user specified prompt ("user prompt") and uses it to generate one or more images based on the use of 
* expando tokens
* expando lookups
* expando meta commands
* expando pipeline commands
* expando batch and sub-prompt delimiters.

## Concept and Process 

A **user prompt** is the prompt (the main/positive prompt) at the time of the script executed, provided by the user

A **user negative prompt** is the value provided by the user as the negative prompt.

The **user pipeline configuration** is the configuration at time of script execution, including the seed value, model, guidance scale, etc. both prompt and negative prompt are not included (or removed)

The two prompts (user prompt, user negative prompt) are combined into the **user parameter set**, a dictionary with a key for prompt and negative prompt. The user pipeline configuration is maintained separately for efficiency.

The *user parameter set prompt value* is examined for **meta commands**. These will have scope over the entire script. They are extracted (and removed) from the prompt and are used to set relevant script scoped flags or values or to set additional parameters on the user parameter set, depending on their function and implementation. 

The user parameters are split into one or more **batch parameter sets**. Using the batch delimiter, the user parameter set prompt and negative prompt are used to generate one or more separate batch parameter set(s).

Each *batch parameter set* has the relevant prompt and negative prompt set from the fragments of the original user parameter set values.  Any parameter sets also inherit any other parameters set by meta commands above. 

Each **batch** and its batch parameter set is iterated over to process the batch and calculate the **actual parameter set list**, an ordered list of generations to perform with specific parameters. 

To do this for each batch parameter set, the following actions take place.

The batch parameter set prompt value is examined for any **batch commands**. There are extracted (removed) from the prompt and set any batch scope variables or flags or batch parameters as required by their functionality. 

The batch parameter set is then interpolated and enriched by reading specific markup on the parameters to generate one or more **batch item parameter sets**. Using the expando tokens, a single batch parameter set may define 1, 5 or 100 different *batch item parameter sets* that combine all the available permutations of the token options.

Each *batch item parameter set* is then split into one or more **potential item parameter sets** based on the presence of an sub-prompt delimiter.

Each *potential item parameter set* prompt value has **pipeline commands** extracted and removed. These are then used to interpolate more possible permutations of pipeline configuration parameters which will generate one or more ***actual parameter sets***

The **Actual parameter set** is a specific and fully resolved set of parameters, including prompt, negative prompt and pipeline configuration values which define exactly 1 image generation. This actual parameter set is accumulated as the **image generations** list  

When all the actual parameter sets are generated from the potential, batch item, batch and user parameter sets. The scope of the generations is known, the user can confirm the output and actual generations begin. 

Before and after each image generation, 'before' and 'after' script executions are performed if defined. The pipeline configuration is carefully reset between each executions to ensure consistency.

The *Actual item specification* is used to trigger the *Draw Things pipeline* using the API.  
## General Script Processing Flow

When all possible mechanisms (tokens, lookups, meta commands, pipeline commands, batches and workflows) are used the flow of the script follows this pseudo code:

``` pseudo-code

def expando

	// initialise
	user_parameter_set = get_user_parameter_set()
	user_pipeline_config = get_pipeline_config()
	user_parameter_set = apply_meta_commands(user_parameter_set)
	
	//interpolate
	image_gens = interpolate(user_parameter_set())
	// NOTE: images_gens an array of arrays of actual parameter sets
	// - the outer array is by batch
	// - the inter array are all the actual parameters within that batch
	
	//confirm execution
	show_confirm_dialog(image_gens)

	//perform image generation
	//for each batch
	for each actual_parameter_set_array in image_gens
		//for each image to generate
		for each actual_parameter_set in actual_parameter_set_array 
			merge user_pipeline_config into actual_parameter_set (priority: actual)
			set pipeline_config(actual_parameter_set)
			run_pipeline
	
	 //clean up and close out
	 set_pipeline_config(user_pipeline_config)
	 anything else. 
```


## Meta Commands

Expando **meta commands** are additions to the user prompt that have scope over the overall script execution.

Meta-commands take the format "meta:command:value" and set global flags or variables or insert values into the user parameters to be propagated down through batches and smaller parameter sets and scopes of operation

Meta commands are found and extracted from the entire user prompt, no matter where they appear. After meta commands are processed, there will be no meta commands remaining in the prompt as it is propagated into batch, batch item, potential item or actual item parameter sets

### Meta Specific Commands

The following meta-commands are unique to the the meta (script layer)

**debug**: Turns on and off different debug settings based on the value. Is consumed, removed from prompt and sets a global variable or flag. 

Available values and effects:
* dryrun: execute script but do not generate any images (don't call Draw things API to trigger pipeline). Also disables any other mutating API access such as interacting with the canvas or saving a file. 
* debug:  turn on debug logging suitable for tracing the execution of the file
* pipeline: output the pipeline config before and after each batch, in addition to prior to each generation. 
* interpolation: output addition information about the interpolation stage, including the size of all arrays, names of lookups accessed.

### Meta Pass-through commands

**(any)**: Any unknown command is passed through and stored on the user parameter set. Because the way parameter sets propage, this means global commands for all batches and pipelines can be set at the meta/global level. Note that lower level commands (batch, pipleline) will override meta command parameters if set. 

### Examples

```pseudo-code

user_parameter_set = {
	prompt:"a black dog (&) a yellow cat meta:debug:dryrun meta:steps:10"
	negativePrompt: ""
}
globals = {}

apply_meta_commands(user_parameter_set) == {
	prompt:"a black dog (&) a yellow cat",
	negativePrompt:"",
	steps:"10"
}
gobals == { 'debug':'dryrun' }

```

## Batches and Batch Delimiter

A user prompt and user negative prompt may contain more than one batch.
The user parameter set which contains both these values is examined. 

The batch delimiter takes the format of '(&)' in the string values of the prompt and negative prompt. 

See example pseudo code for behaviours

```pseudo-code

// if no batch delimiter, return one batch
user_parameter_set = {
'prompt': 'a dog',
'negativePrompt': 'blurry',
'steps': '10',
...
}
get_batches(user_parameter_set) == [
{'prompt':'a dog','negativePrompt':'blurry','steps': ...}
]

// if only one negative Prompt batch, use for all. always copy other params as well 
// NOTE: an empty negative Prompt ('') counts as one. 
user_parameter_set = {
'prompt': 'a dog(&)a cat'
'negativePrompt': 'blurry'
'steps': '10'
}
get_batches(user_parameter_set) == [
{'prompt':'a dog','negativePrompt':'blurry','steps': '10'},
{'prompt':'a cat','negativePrompt':'blurry','steps': '10'}
]

//if exactly the same number of batches in prompt and negative prompt, zip them up and return together
user_parameter_set = {
'prompt': 'a dog(&)a cat'
'negativePrompt': 'blurry(&)low quality'
'steps': '10'
}
get_batches(user_parameter_set) == [
{'prompt':'a dog','negativePrompt':'blurry','steps':'10'},
{'prompt':'a cat','negativePrompt':'low quality','steps':'10'}
]

//if negativePrompt does not have 1 or exactly the same number of batches, error
user_parameter_set = {
'prompt': 'a dog(&)a cat'
'negativePrompt': 'blurry(&)low quality(&)too many hands'
'steps': '10'
}
get_batches(user_parameter_set) ==> Error


```

## Batch Commands

Expando **batch commands** are additions to the user prompt that have scope over the batch they are included with.

 batch commands take the format "batch:command:value" and set batch level flags or variables or insert values into the batch parameters to be propagated down through batch items and smaller parameter sets and scopes of operation.

If the same batch command appears multiple times, only the last one processed is considered. A warning is written to the console in this case but script execution continues.

```pseudo-code

//batch commands are naturally split into the batch parameter sets depending on which fragment of the user prompt they are in
user_parameter_set = {
'prompt': 'a dog batch:maxbatchitems:1(&)a cat batch:maxbatchitems:2'
'negativePrompt': 'blurry'
'steps': '10'
}


batch_parameter_sets = get_batches(user_parameter_set) == [
	{'prompt':'a dog batch:maxbatchitems:1', ...},
	{'prompt':'a cat batch:maxbatchitems:2', ...}
]

//duplicated batch commands take the last value specified
user_parameter_set = {
'prompt': 'a dog batch:maxbatchitems:1 batch:maxbatchitems:2'
'negativePrompt': 'blurry'
'steps': '10'
}

batch_parameter_sets = get_batches(user_parameter_set) == [
{'prompt':'a dog batch:maxbatchitems:2', ...},
]

```
### Batch Specific Commands

The following batch commands are unique to the the batch layer. These are removed from the prompt and set batch level variables or flags. 

**maxbatchitem** takes a numeric value which will indicate the maximum number of batch items which will be made from this batch. Note: There is a default value of 100 batch items to be created from any batch. This is overridden by this value if provided.

For example, the prompt "A [color] dog batch:maxbatchitem:10", will cause a maximum number of 10 batch item parameter sets to be populated for this batch and never more, even if the color lookup has 20 values. 

**sample** works like *maxgens* except the batch items are selected at random from the all possible match items.

For example, if the color lookup contains 5 different colors, "a [color] dog batch:sample:2" will limit batch items to 2.

### Batch Pass-through commands

**(any)**: Any unknown command is passed through and stored on the batch parameter set. Because the way parameter sets propagate, this means batch commands will propage as parameters into batch item, potential item and actual item parameter sets. Batch commands passed through as parameters will override any existing parameter (probably from a meta command) specified. Note that lower level commands (pipeline), will override batch command parameters if set. 

## Batch Interpolation

After the *batch commands* are processed, the *batch parameter set* is processed using the expando tokens to transform and multiply the number of items into a set of one or more **Batch Item Parameter sets**.

Expando-Tokens in the script can be identified as any non-nested set of characters within square brackets. These can be in the prompt or negativePrompt

Example inputs presented here are all assumed to be from the batch parameter set. 

Examples:
For the prompt: "A [white,black] dog", there is one expando-token, "white,black"
For the prompt: "A [white,black] dog jumping over a [chair,bed]", then there are two expando-tokens, "white,black" and "chair,bed"

Each expando-token is resolved into one or more options for replacement of that part of the prompt/negative prompt. All of those options within the limits discussed within this document, are created in all permutations as **Batch Item Parameter Sets**

The techniques that discuss how expando-tokens are resolved are described in this section, and include:
* inline lookups
* predefined lookups
* nested lookups
* repeated lookups
* back references

If there are no expando-tokens present, the batch parameter set results in one batch item parameter set with no modifications. 

Note that sub-prompts and and actual item interpolation are effectively ignored at batch interpolation time, meaning that the resolution of lookups and back references happens across the scope of both while they are expressed as batch items. 

Note that the number of batch item parameter sets generated must be halted when the maxbatchitem (default:100, overridable with a the batch command maxbatchitems) is reached. This limit is for each batch. 

If the generation of batch item parameters is halted due to reaching the maxbatchitem limit, the script progression continues, but a warning is written to the console and it will be noted on the user confimation dialog.

### Inline Lookups

Inline lookups, found in expando tokens, provide all of the options available inline in the token within the prompt and negative prompt, separated by commas. 

For example, the format [x,y] creates 2 options, an option with x and an option with y

The prompt "A [white,black] dog" will generate two options for generation:
- "A white dog"
- "A black dog"

When more than one value is in a prompt, it adds multiplicatively to the batch item parameter sets.

For example, "A [white,black] dog jumping over a [chair,bed]" creates 2 options for each inline lookup, with the result being that there are 2x2 = 4 options, and therefore 4 batch item parameter sets for generation:
* A white dog jumping over a chair
* A white dog jumping over a bed
* A black dog jumping over a chair
* A white dog jumping over a bed

Using only literal lookups, the total number of options generated will be the total number of permutations of the values from each position, or the length of each literal lookup multiplied by each other. 

For example, for the prompt "[a,b,c]  [d,e]  [f,g]" the total number of permutations and therefore options (and therefore batch item parameter sets) will be 3 x 2 x 2 = 12. 

The following formats should be supported:
* "[x,y]" - x and y are both options. 
* "[x,y,]" - 3 options: x, y and an empty string 
* "[x]" - 1 option only. The same as not using an expando-token
* "[x,y,z:1]" - 1 option only, selected randomly from x,y and z
* "[x,y,z:2]" - 2 options only, selected randomly from x,y,z, but the same option can not be repeated

The follow is a pseudo code example of the above principles:

```pseudo-code

// no tokens included, one output the same as the batch parameter set
batch_parameter_set = {
'prompt': 'a dog'
'negativePrompt': 'blurry'
'steps': '10'
}
batch_item_parameter_sets = interpolateBatch(batch_parameter_set) == [
	{ 'prompt': 'a dog', 'negativePrompt': 'blurry', 'steps': '10'}
]

// two literal tokens included, one batch_item_parameter_set for each combination
batch_parameter_set = {
'prompt': 'a [black,white] dog jumping over a [bed,table]'
'negativePrompt': 'blurry'
'steps': '10'
}
batch_item_parameter_sets = interpolateBatch(batch_parameter_set) == [
	{ 'prompt': 'a black dog jumping over a bed', ... },
	{ 'prompt': 'a black dog jumping over a table', ... },
	{ 'prompt': 'a white dog jumping over a bed', ... },
	{ 'prompt': 'a white dog jumping over a table', ... },
]

//literal tokens in both normal and negative prompt
batch_parameter_set = {
'prompt': 'a [black,white] dog'
'negativePrompt': '[blurry,low quality]'
'steps': '10'
}
batch_item_parameter_sets = interpolateBatch(batch_parameter_set) == [
	{ 'prompt': 'a black dog jumping over a bed', 'negativePrompt': 'blurry', ... },
	{ 'prompt': 'a black dog jumping over a table', 'negativePrompt': 'blurry', ... },
	{ 'prompt': 'a white dog jumping over a bed', 'negativePrompt': 'low quality', ...  },
	{ 'prompt': 'a white dog jumping over a table', 'negativePrompt': 'low quality', ...  },
]
```
### Predefined Lookups

The script pre-defines a limited number of lookups. Each value of an inline lookup is evaluated against the list of predefined lookups to see if a predefined lookup is being invoked. If matched, an option is resolved against all of the matching values in the lookup. If a lookup of that name is not found, the option is treated as a literal as per the normal rules above. 

For example, the script might define a 'color' lookup containing the values 'white' and 'black'. The prompt "A [color] dog" would then resolve to the following prompts in different *batch item parameter sets*:
* A white dog
* A black dog

Using only different predefined lookups, the total number of options generated will be the total number of permutations of the values from each lookup, or the length of lookup multiplied by each other. 

For example, for the prompt "[color]  [shape]  [texture]" the total number of permutations and therefore options (and therefore batch item parameter sets) will be the length of the 'color', 'shape' and 'texture' predefined lookups multiplied together. 

### Mixing Predefined Lookups with Inline Lookups

Inline and predefined lookup options can be mixed. in the above example where there is a 'color' lookup containing black and white, the following prompt "A [color,green] dog" would result in the following prompts: 
* A white dog
* A black dog
* A green dog

Note that a mixed lookup, like nested lookups, resolves its values prior to use by substituting the reference to the predefined lookup for the values from the lookup. So '[color,green]' resolves to ['white','black','green'], where 'color' is replaced by the values in the associated predefined lookup.

Other inline conventions are also followed. Assuming the color lookup still only has 'white' and 'black' options:
* [color:2] randomly selects 2 values from the 'color' lookup that aren't duplicates and uses these to generate options
* [color,] uses all the values from the 'color' lookup (2) and an additional empty string value, for a total of 3 additional values and three separate additional permutation options ('white','black' and '')
* [color,green,] uses all the values from the 'color' lookup (2) and add a 'green' and '' value for a total of 4 values generating 4 additional permutation values. 

Note the formats of '[shape:2]' and '[color,green]'  modify the options created as you would expect, changing the number of values available and therefore the number of options created through the available permutations.

For example
* considering the prompt "cars shaped like [shape:2] and painted [color,green]"
* if the 'shape' lookup has 5 values and the 'color' lookup has 4 values, 
* the total number of options created would be the number of shape values available (only 2, because of the ':2') multiplied by the number in the second lookup (5, the four from the predefined lookup 'color' plus the literal 'green')
* this makes for a total 2x5=10 different options (permutations) 
### Repeating Lookups 

Predefined Lookups can be repeated in a prompt, but the same value is not available for each subsequent same predefined lookup for that option. 

For example, for the prompt "The girl wore a [color] dress and a [color] hat", the combination of 'black' and 'black' (ie "the girl wore a black dress and a black hat") is not possible. 

In this example, if the 'color' lookup has 4 values, this means that only 12 options are created by the above prompt: 4 colors to choose from for a dress and 3 for the hat (since 1 option will always be consumed when the dress color is resolved)

### Lookup Aliases

The user might want the same lookup to be treated completely independently when it is repeated. To achieve this they can effectively alias the lookup by adding a numbered suffixed to the name of the lookup in the following format. In effect this gives each lookup a type (the array that is used to fine values) and a instance name.

A lookup alias has the following format: '[lookup_N]', where is *lookup* is the normal name for the lookup (E.g. 'color') and *N* is a digit between 0 and 9.

An aliased lookup does not share the same remaining or used values for the current combination (depending on the implementation), allowing some repeats of the same lookup value at mutiple places in the prompt . 

Consider the prompt: "The girl wore a [color] dress and a [color_1] hat". In this case, the color lookup is used in both lookup locations. However, unlike normal repeating lookups, the value can be repeated, since the color_1 alias has its own list of remaining or used values. So a valid evaluated combination would be 'The girl wore a black dress and a black hat'.

In this example the total number of options generated for a 'color' lookup of 4 values is 4 for 'color' and 4 for the aliased predefined lookup 'color_1', or 4 x 4 = 16 options generated. 

Each predefined lookup or alias can still be repeated within the prompt and retain the duplication free feature. The prompt "The girl wore a [color] dress and a [color_7] hat, and [color] shoes" will mean the dress and the shoes will never be the same color, but the hat may have the same color as either dress or shoes.

In this example, again assuming 'color' has 4 values, the total number of options generated will be: 4 (1st color) x 4 (1st color_7) x 3 (2nd color) or 48 new options in total .
### Back References

Sometimes the same lookup value in a different parts of the prompt is desired. The back reference binds a lookup value to an older lookup value previously processed. 

A back reference is in the format: '[=lookup_or_lookup_alias]' where *lookup_or_lookup_alias* is a normal lookup name or alias (see above).

A back reference will force the lookup resolution to find the previously selected value for that lookup or lookup alias and use that, circumventing the need to do further resolution. 

Because of this, a back reference doesn't add any new options, since the value is dictated by the value chosen for the previous use of that lookup. 

For example, the prompt: "The girl wore a [color] dress and a [=color] hat" will mean the dress is always the same color as the hat. If 'color' lookup has 4 values, only 4 options are created since there will only ever be one value of [=color].

This works with aliases and more complicated examples as well. The prompt "The girl wore a [color] dress and a [color_7] hat, and [=color_7] shoes" means the hat and shoes will always be the same color. 

#### Back References - Edge Cases

* if the back reference appears before its original lookup or lookup alias, its value is set as the first option in the referenced lookup. A warning is written to the console. 
* Like all batch interpolation, sub-prompts and the presence of the sub-prompt delimiter is ignored, so a back reference in a second sub-prompt can refer to the result of a lookup in t he first. 

### Nested Lookups

The values of a predefined lookup can reference other predefined lookups to be evaluated, substituting the reference to the other predefined lookup with the values from that predefined lookup. 

For example, if the predefined lookup "age" is defined it might contain the values "child", "adult" and "elderly". If the predefined lookup "child" is defined it might contain the values "baby", "toddler", "preteen" and "teenage". If no other lookups are defined for adult and elderly the following prompt:
"A [age] male" would result in 6 options:
* A adult male
* A elderly male
* A baby male
* A toddler male
* A preteen male
* A teenage male  

*Infinite recursion must be avoided*. In resolving a specific token, the same nested lookup can not be used more than one. This makes maximum recursion depth unspecified, but if a lookup cannot be used more than once, the maximum recursion will be limited to the number of lookups as a maximum. 

ie. Instead of lookup A --> B --> A --> B (recurring), the script should allow A -->B but not A --> B --> A. A warning should be written to console that B tried to nest A but A had already been evaluated should be written to console, but execution should continue.

Note that a nested lookup, like a mixed lookup, resolves its values prior to use by substituting the reference to the predefined lookup for the values from the lookup. So '[age]' resolves to ['child','adult','elderly']. 'child' is then replaced with its values, making ['baby',toddler','preteen', 'teenage','adult','elderly'].

Because a lookup can be repeated referenced in a prompt (see above), the above check for recursion must be independent for each token expansion. 
### Initial lookups and lookup definition

Initially, the following lookups will be defined with a limited number of values in the script. These will be defined in a way easy to add new lookups and lookup values in the script, so will only be defined in one place.

The following lookups are initially predefined within the script. 
* colors: red, green, blue etc
* shapes: circle, square, ...

The definition of these lookups will allow easy expansion of lookup values and lookups within the script.

E.g 
```
// Example look up structure
const predefinedLookups = {

	// to add a new lookup would you would add a key with the name of the lookup so it is automatically used
	// to add a new lookup value you would update the relevant array

	"color": ["white", "black", "red", "blue", "green"],
	"shape": ["square", "circle", "triangle", "fun_shapes"],

	// a potentially nested lookup is defined the same way.
	// it can still be called directly (unnested)
	"fun_shapes": ["star"],


};
```

### Batch Interpolation: Putting it all together

The following  example is intended to illustrate how the above rules come together with a non-trivial example to interpolate a *batch parameter  set* to define one or more *batch item parameter sets*

Note: Further interpolation happens at for the *potential item parameter set* and the *actual item parameter set*, but these are independent and downstream of the resolution of expando tokens and the options generation that occurs here to create the *batch item parameter sets.*

```pseudo code

// Example
const predefinedLookups = {
	'color': ['white', 'black', 'blue', 'reds']
	'reds': ['lipstick red', 'pink', 'maroon']
}

batch_parameter_set = {
	prompt: 'Girl wearing a [color:2] [cocktail,summer] dress and [color,] shoes and a large [color_1] hat and [=color_1] scarf'
	negativePrompt: '[blurry,low quality]'
	steps: 10
}
```

Working through the prompts lets examine each expando token to understand how it is handled and creates options (where 'options' a single set of resolved values in a Batch Item Parameter Set)

For the prompt:

* '[color:2]' - this is a predefined lookup of 4 values, but one of the values ('reds') will match the name of another predefined lookup, after substituting that lookup in, there are 6 unique values. The ':2' part of the token means that we can only consume 2 unique values from it. This prompt therefore doubles the original one option of the prompt if it had no tokens. (1 x 2 = 2 options total so far)
* '[cocktail,summer]' - this is an inline lookup of 2 values. both values will contribute. This will double the number of options formed. (2 x 2 = 4 options so far) 
* '[color,]' - this is a predefined lookup of color (resolving to 6 as before) with the addition of an empty string. Any of these 7 values could be used, with the constraint that the same value of color can not be used. With that constraint, only a factor of 6 (7-1) more options are created. (4 x 6 = 24 options so far).
* '[color_1]' - this an alias for the color predefined lookup, and as such has 6 possible values. None have been consumed, so the number of options increases by another factor of 6. (24 x 6 = 144 options so far)
* '[=color_1]' - this is a back reference. As such it can only have one value, the value of color_1 chosen previously in this forming option. The options are not increased (or only do so by a factor of one). (144 x 1 = 144 options so far)

The negative prompt also contributes:
* one original option if the tokens are not evaluated (1 option so far)
* '[blurry,low quality]' - an inline lookup with 2 values, doubling the number of options available (144 x 2 = 288 options total)

Note that the number of batch item parameter sets generated must be halted when the maxbatchitem (default:100, overridable with a batch command) is reached. Since this was not provided, only 100 options and there *batch item parameter sets* will be generated. 

A *batch item parameter set* has the same structure as the *batch parameter set*,but all expand token references are resolved in the prompt and negative prompt. Other parameters, if present, in the *batch parameter set*, are copied.

A example of valid generated *batch item parameter sets* are provided below for this example:  

```pseudo code

batch_item_parameter_sets = interpolateBatch(batch_parameter_set) == [
	...,
	{ 
		'prompt': 'Girl wearing a blue cocktail dress and pink shoes and a large pink hat and blue scarf', 
		'negativePrompt': 'blurry'
		'steps': 10
	},
	...,
	{ 
		// note the empty string used for the [color,] expando token
		'prompt': 'Girl wearing a maroon cocktail dress and  shoes and a large blue hat and white scarf', 
		'negativePrompt': 'low quality'
		'steps': 10
	},
	...,
]

// Max batch items setting enforced, other would be 244
batch_item_parameter_sets.length = 100
```


## Sub-prompts and  Sub-Prompt Delimiter

After the *batch item parameter sets* have been generated, each of these are split using the **Sub-prompt delimeter** to form **potential item parameter sets**.

The Sub-prompt delimited has the format of '||' and indicates where prompts and negative prompts should be split into sub-prompts for separate image generation executions. If there are no sub-prompt delimiters, then the whole body of the prompt or negative prompt is used as the single sub-prompt.

If the negative prompt has one sub-prompt and the main prompt has multiple sub-prompts,the same negative prompt is used for all generated potential item parameter sets. If the negative prompt has exactly as many sub-prompts as the main prompt, these are zipped together in order. If the negative prompts has more than one sub-prompt, but isn't the same number as are found in the main prompt, an error occurs. 

See the following example to show how *potential item parameter sets* are created. 

```pseudo-code

// if no sub-prompt delimiter, return one potential item 
batch_item_parameter_set = {
'prompt': 'a dog',
'negativePrompt': 'blurry',
'steps': '10',
}

get_potential_items(batch_item_parameter_set) == [
{
	'prompt': 'a dog',
	'negativePrompt': 'blurry',
	'steps': '10',
}

// if mutiple sub-prompts appear in the main prompt but not in the negative prompt, use the same negative prompt sub-prompt
// if no sub-prompt delimiter, return one potential item 
batch_item_parameter_set = {
'prompt': 'a dog||a cat',
'negativePrompt': 'blurry',
'steps': '10',
}

get_potential_items(batch_item_parameter_set) == [
	{
		'prompt': 'a dog',
		'negativePrompt': 'blurry',
		'steps': '10',
	},
	{
		'prompt': 'a cat',
		'negativePrompt': 'blurry',
		'steps': '10',
	}
]

// if mutiple sub-prompts appear in the main prompt and the same number in the negative prompt, zip them up in order. 
batch_item_parameter_set = {
'prompt': 'a dog||a cat',
'negativePrompt': 'blurry||low quality',
'steps': '10',
}

get_potential_items(batch_item_parameter_set) == [
	{
		'prompt': 'a dog',
		'negativePrompt': 'blurry',
		'steps': '10',
	},
	{
		'prompt': 'a cat',
		'negativePrompt': 'low quality',
		'steps': '10',
	}
]

//If there is more than sub-prompt in the negative prompt but this doesn't match the number of sub-prompts in the main prompt, this is user error.
batch_item_parameter_set = {
'prompt': 'a dog',
'negativePrompt': 'blurry||low quality',
'steps': '10',
}

get_potential_items(batch_item_parameter_set) ==> Error

```

## Pipeline Commands


**pipeline commands** are additions to the user prompt that have scope over the sub prompts (only) that  they are included with. Pipeline commands represent either: 

* the execution of additional self contained code (scripted pipeline commands)
* additional variable configuration of the other pipeline settings, or (parameter pipeline commands)

Pipeline commands only apply to potential item parameter sets, which capture at the sub-prompt level prior to interpolation there and after the batch interpolation phase. 

Pipeline commands take the format "pipeline:command:value" and interact with the non-prompt parameters of a *potential item parameter set* to be interpolated or propagate to *actual item parameter sets*.

Note the 'value' for pipeline commands may have a special format for further interpolation which is NOT performed here. The command is also not validated, but is accepted as presented.

pipeline commands must be extracted from the prompt when they are found. 

All  pipeline commands work the same way; They are processed into the parameters of the potential item parameter set and are removed from the prompt. 

Note: Pipeline commands override any other parameters with the same name if it exists. 

### Valid Parameter Pipeline Commands

valid parameter pipeline commands to be handled include:

pipeline:seed:1 ==> parameter key 'seed', value '1'
pipeline:seed:-1 ==> parameter key 'seed', value '-1'
pipeline:steps:10 ==> parameter key 'steps', value '10'
pipeline:steps:4,5,6 ==> parameter key 'steps', value '4,5,6'
pipeline:t5encoding:false ==> parameter key 't5encoding', value 'false'

```pseudo-code

//example parameter pipeline commands in potential item parameter set
potential_item_parameter_set = {
	'prompt': 'a dog pipeline:seed:1',
	'negativePrompt': 'blurry',
	'steps': '10'
}


process_pipeline_commands(potential_item_parameter_set) == 
{
	'prompt': 'a dog',
	'negativePrompt': 'blurry',
	'steps': '10',
	'seed' : '1'
}

//example pipeline commands in potential item parameter set
potential_item_parameter_set = {
	'prompt': 'a dog pipeline:guidanceScale:4,5,6 pipeline:steps:20',
	'negativePrompt': 'blurry',
	'steps': '10'
}


process_pipeline_commands(potential_item_parameter_set) == 
{
	'prompt': 'a dog',
	'negativePrompt': 'blurry',
	'steps': '20', //overridden
	'guidanceScale' : '4,5,6'
}

```
### Valid Scripted Pipeline Commands

Valid scripted pipeline commands are ones with an implementation in the script. The script is introspected by itself during the Resolve Accumulated Parameters phase to ensure this is correct. Since there can be multiple script commands 'before' and 'after', these are added to an array on the 'before' and 'after' parameters.

Note: A separate list of valid scripted pipeline commands is not kept. During validation the script is introspected for functions matching the naming convention pipeline_script_[name] with the expected function signature.

```pseudo-code

//example parameter scripted pipeline commands in potential item parameter set
potential_item_parameter_set = {
	'prompt': 'a dog pipeline:after:detail_face',
	'negativePrompt': 'blurry',
	'steps': '10'
}


process_pipeline_commands(potential_item_parameter_set) == 
{
	'prompt': 'a dog',
	'negativePrompt': 'blurry',
	'steps': '10',
	'after': ['detail_face']
}
```

## Actual Item Interpolation

*Potential Item Parameter Sets* must be interpolated to **Actual Item Parameter Sets**

This involves: 
* interpolation of any additional options from parameters that can be interpolated. 
* resolving all accumulated parameters to the correct parameter name (see appendix) and type and removing (with console warning) invalid parameters remaining. 

### Interpolating from Parameters

* Every potential item parameter set implies one generated *actual item parameter set*
* Any parameter values found with a comma separation imply additional options which will increase the number of actual item parameter sets created. 

```pseudo-code

potential_item_parameter_set = {
	'prompt': 'a dog',
	'negativePrompt': 'blurry',
	'steps': '10,12',
	'after': 'face_detailer'
}

get_actual_items(potential_item_parameter_set) == [
	{
		'prompt': 'a dog',
		'negativePrompt': 'blurry',
		'steps': '10', //varies
		'after': 'face_detailer'
	},
	{
		'prompt': 'a dog',
		'negativePrompt': 'blurry',
		'steps': '12', //varies
		'after': 'face_detailer'		
	}
]
```

### Resolving Accumulated Parameters

#### Resolving Pipeline Script Commands

'before' and 'after' parameters are pipeline script commands. To be resolved each value in the 'before' and 'after' parameter array is checked against an introspection of the available functions in the script. Commands that are valid will be defined in the script as functions named in the format 'pipeline_script_name' where name is the value of the item from the 'before' or 'after' parameter array. Allowance should be made for discrepancies in case, and the full, correctly capitalised function name (as appears in the script) used to replace the value.

A script maybe appear more that one in its array, or in both 'before' and 'after' parameter arrays, since there are use cases for this method of operation. 

Note: A separate list of valid scripted pipeline commands is kept. During validation this list is used to validate that the name of the script is valid. This is case insensitive. 

If the function does not exist a warning is output to the console that includes the function name which would have matched command. Functions not found are removed from the 'after' or 'before' parameter array. 
#### Resolving Pipeline Parameter Commands

All other parameters should be resolved against the supported parameters of the pipeline or removed. Allowance should be made of incorrect case, and an additional set of aliases should be maintainable within the script.

The values should be changed to the relevant type expected by the api. Any value which cannot by coerced into the correct type should cause an error to be thrown and logged to console, but execution will continue without that parameter. Parameter values have no other range checking and the Draw Things API will detect these. 

A table of allowable parameters is in the appendix.

```
const parameter_aliases = {
	'cfg':'guidanceScale',
	'guidance':'guidanceScale',
	// user maintainable in the script
}


actual_item_parameter_set = {
	'prompt': 'a dog',
	'negativePrompt': 'blurry',
	'steps': '10', 
	'cfg': '2', 
	'gherkin': 'hello'
	'Strength': '1'
	'before' : ['test','i_dont_exist]
	'after': ['test', 'face_detailer']
}

resolve_parameters(potential_item_parameter_set) == {
	'prompt': 'a dog',
	'negativePrompt': 'blurry',
	'steps': 10, //valid, changed to number
	'guidanceScale': 2, //mapped from alias, changed to number
	//gherkin removed - not valid nor aliased
	'strength': 1 //wrong case but still matched, value changed to number
	'before': ['pipeline_script_test'] // 'i_dont_exist' removed because it didn't exist
	'after': ['pipeline_script_test', 
		'pipeline_script_face_detailer'] //resolved function names
}
```

## User Confirmation

Before generation commences but after all *actual item parameter sets* are resolved, a confirmation dialog appears.

User confirmation appears once for all batches, and commences image generation for all actual item parameter sets across all batches. 

The following information will be shown:
* The total number of batches found
* The total number of image generations that will be performed (equals total number of actual item parameter sets across all batches)
* For each batch:
	* Batch number (e.g. 1)
	* Total number of image generations (just the total actual item parameter sets from that batch)
	* The fist (only) actual item parameter set should be displayed. This will include the prompt, negativePrompt, and other parameters defined. 
	* Whether the batch item generation was limited by hitting the maxBatchItem limit.
* An option to Cancel or proceed. 
* If the number of image generations exceeds the maximum image generation limit (1000), a warning will be shown.

## Image Generation

If the user proceeds from the confirmation dialog, the images will be generated. 

All image generation is done together across all batches and their actual item parameter sets. 

The pipeline is prepared by setting the following configuration 
* strength:1

In order to generate the images, the script iterates over the actual item parameter sets and uses the Draw Things pipeline API to set the configuration and run the pipeline to generate the image.

### Iterating over Actual Item Parameter Sets

The core loop of image generation is an iteration over the actual item parameter sets. 

The number of image generations will not exceed the image generation maximum of 1000 generations (defined in a user editable value in the script). If it is exceeded a warning is written to the console log and image generation stops, but the script continues. 

### Before Each Image Generation

Before each image generation, the following is done: 
1. The script outputs the count and total image generations to be performed to the console
2. The 'before' and 'after' parameters in the actual item parameter set, if they exist, are extracted and removed.
3. If a 'before' parameter exists, execute the  functions with the names matching the parameter array item values with the standard arguments (see below). This must be done before the pipeline is configured below.
5. A pipeline configuration is determined. This is done by merging the *actual item parameter set* with the *user pipeline configuration* , such that the actual item parameter set parameter overrides the user pipeline configuration where the same parameter exists in both. 
6. This new pipeline configuration is used to configure the pipeline using the Draw Things API. 
	
### After Each Image Generation

After each image generation the following is performed:

1. If a 'after' parameter exists, execute the  functions with the names matching the parameter array item values with the standard arguments (see below). This must be done before the pipeline is reset below.
2. The user pipeline configuration should be used to reset the pipeline configuration after each image generation

### Functions run with 'Before' and 'After' functions

The function names will be stored in the actual item parameter set's 'before' and 'after' parameter arrays and would have been validated earlier. The signature of the functions is: 

function pipeline_script_name(parameter_set, current_execution_context)

The current execution context provided to the function is a structure with the following values:

* whether this script is being run 'before' or 'after'
* current batch number being processed
* current potential item number being processed (ie. the number prior to working out the sub-prompts.)
* current actual item number being processed (the actual image generation number)

Other information may be added in the future that would be useful a script to consume. 

Note: If a function throws an exception, a warning and details are written to the console but the execution of the script continues. 

#### Available Pipeline Script Options

* **test**: This is a simple parameter script command that outputs a message to the console to confirm execution of the script, that it is being run 'before' or 'after' the current image generation number.
* **reset_canvas**: This is a simple parameter script that uses a Draw Things API call to reset the canvas. It looks a message to the console to confirm that is has done this. 
* **face_detailer**: This an 'after'-only script command that executions an additional image generation around a detected face to increase the detail and quality of rendered faces. 

## Performance Considerations

Because this script operated through combinatorial exploration of different permutations, performance issues - especially during interpolations on user prompts with many large lookups - may be apparent.

The risk to stability from memory use or the risk of unacceptable interpolation time is managed by the both the maxBatchItem command and default (100 batch item parameter sets) and the image generation limit (1000)  serve to protect against performance risks. Note: Even if it can be predicted that limits will be reached, the script should generate parameter sets and images up to that point and execute - no early termination. 

Performance optimisations that should be considered include:

- Caching of resolved predefined lookup values. The cached version should include values from nested lookups. This should happen on first use, since large lookups might not be invoked by the inclusions in the prompt
- Avoiding evaluation of batch item parameter sets and their combinations above the maxbatchitem limit
- Optimising of the meta:sample command such that not all possible batch item parameter sets must be resolved while still showing a representative and diverse set of generations. 

## Error and Exception Handling

* Tight regular expression matching should be used to exclude incorrect formats
	* Expando markup sent to Draw Things because it was not matched is not fatal
* In most cases, errors should be reported to the console but execution continued. 
* Invalid command formats (meta, batch, pipeline) will either be left on the prompt and set as a part of the prompt or be captured and propagated as parameters and later cleaned up.  
* Reference lookups, if not found, will cause the script to naturally treat them as inline lookups. Execution will continue
* Invalid parameter values sent to the draw things API will be reported separately by the draw things API but will not stop execution

## Other and Edge Conditions

* There is a fallback prompt if it is not set.
* The default MaxBatchItems value is 100
* There is a hardcoded maximum of 1000 generations,. This can be changed by altering a value in the script. 


## Appendix - Configuration Keys

The following debug output shows a non-exclusive list of available configuration keys. Types can be implied by the values output. 

```
separateOpenClipG: false, 
aestheticScore: 6, 
shift: 1, 
diffusionTileWidth: 1024, 
stage2Steps: 10, 
id: 0,
diffusionTileHeight: 1024, 
motionScale: 127, 
negativeOriginalImageHeight: 512,
upscalerScaleFactor: 0, 
fps: 5, 
t5TextEncoder: true, 
model: sdxl_lightning_dreamshaperxl_lightningdpmsde_f16.ckpt, 
negativeAestheticScore: 2.5, 
imageGuidanceScale: 1.5, 
stage2Shift: 1,
hiresFixWidth: 960, 
negativeOriginalImageWidth: 512, 
preserveOriginalAfterInpaint: true, 
diffusionTileOverlap: 128, 
numFrames: 14, 
hiresFix: false, 
stochasticSamplingGamma: 0.3, 
maskBlurOutset: 0, 
tiledDecoding: false, 
width: 1024, 
decodingTileHeight: 640, 
cropLeft: 0, 
guidingFrameNoise: 0.02, 
cropTop: 0, 
separateClipL: false, 
batchSize: 1, 
batchCount: 1, 
imagePriorSteps: 5, 
strength: 1, 
refinerStart: 0.85, 
clipWeight: 1, 
clipSkip: 1, 
zeroNegativePrompt: false, 
hiresFixStrength: 0.7, 
startFrameGuidance: 1, 
originalImageWidth: 1024, 
resolutionDependentShift: true, 
controls: , 
steps: 3, 
tiledDiffusion: false, 
loras: ,
sharpness: 0, 
originalImageHeight: 1024, 
maskBlur: 1.5, 
targetImageWidth: 1024, 
seedMode: 2, 
decodingTileWidth: 640, 
speedUpWithGuidanceEmbed: true,
targetImageHeight: 1024, 
negativePromptForImagePrior: true,
seed: 5,
stage2Guidance: 1,
sampler: 4, 
hiresFixHeight: 960,
height: 1024, 
guidanceEmbed: 3.5, 
decodingTileOverlap: 128, 
guidanceScale: 1
```