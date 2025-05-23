# Art Factory Domain Concepts

This document defines the core domain model and business concepts that drive the Art Factory application.

## Domain Model Entities

## Providers

A provider is a service that can be used to generate products (images, videos, etc.)
Each provider has a set of available *models* grouped into *model families*.
Each provider will have their own local or remote API to interact with.

Usage:
- A provider is made available by a provider class.
- A provider has configuration defined such as API keys, etc
- A provider provides *ProductFactory* implementations
- A provider provides the *models* it supports grouped by *model type* and *model family*

Examples:
- Replicate
- fal.ai
- civitai

## Model Modality

Each model has a modality. This is a simple label or enum value that is used to distinguish the expected input and ouput modalities of the model.

Examples:
- Text-to-Image
- Text-to-Video
- Text-to-Audio
- Image-to-Image
- Image-to-Video

## Model Families

Each model family is a collection of models that share a common set of features and capabilities.

Examples:
- Stable Diffusion
- Midjourney
- OpenAI

## Product Factory

A Product Factory is an implementation made available by a provider for the purpose of specifying how the provider is used for a specific generative task based on a *model*.

Each factory implementation has a specific inheritance hierarchy that is optimized for code reuse and distinguishing *model modality*, *model* and *provider* differences. The factory hierarchy includes:

* BaseProductFactory: Common validation and infrastructure
  - Defines base parameter validation logic
  - Provides common utility functions
  - Standardizes error handling and logging

* ProviderProductFactory: Provider-specific setup (e.g., ReplicateProductFactory)
  - Handles provider authentication (e.g., API keys)
  - Manages provider-specific client initialization
  - Implements provider API interaction patterns

* ModelModalityProductFactory: Model modality specifics (e.g., ReplicateTxtToImgProductFactory)
  - Defines common parameters for the modality
  - Specifies output formats and handling
  - Implements modality-specific validation

* ModelSpecificFactory: Model-specific parameters (e.g., ReplicateTxtToImgFluxProductFactory)
  - Sets model-specific parameter defaults
  - Adds specialized parameters or constraints
  - Provides model-specific validation rules


For example, all product factory implementations may share a base factory class that provides common functionality such as validating *generation parameter set* based on a *parameter set spec*

Responsibilities:

* Defining parameter specifications and validation rules
* Converting generic requests to provider-specific calls
* Providing UI hints and default values
* Handling provider API interaction
* Handling provider-based limits to concurrency, rate limits or usage quotas

### Implementation

Each factory has a generic interface that is implemented by a factory class.
Each factory is responsible for
- validating and dispatching *generations* to the real service using the provided *generation parameter set* to determine a *actual parameter set*.
- updating the generation with the *return parameter set* and other metadata results
- making avalable the returned digital assets used to create the *products*

### Other uses

A factory can also be defined to perform a non-generative AI task as required. For example, a factory might resize an asset using a library. 

## Parameter Specifications (ParameterSpecSet)
Each factory defines its parameters using a specification structure: A set of ParameterSpecs defining the parameters it accepts and their constraints upon them.

```
interface ParameterSpec {
  required: boolean;
  type: ParameterType;
  default?: any;
  hint?: string;
  validationRules?: ValidationRules;
  interpolation: InterpolationType;
  uiHints?: UIHints;
}
```

Parameters can specify:

* Required/optional status
* Data type and validation rules
* Default values
* Interpolation capabilities
* UI display hints

Examples of parameters include inference steps, guidance scale, negative prompts, and model-specific options. The specification structure allows factories to:
- Validate parameter sets before generation
- Guide UI construction with appropriate inputs
- Define interpolation behavior for parameter values
- Set sensible defaults per model/provider

### Validation Rules

Each parameter spec can define validation rules including:
* Minimum/maximum values for numeric types
* Pattern matching for strings
* Enumerated valid values
* Custom validation functions

The rules ensure that generation parameter sets are valid for the specific provider, model type, and model being used.

### UI Hints

Factories provide UI hints through the parameter specification to help construct appropriate input forms:
* Input control type (text, number, select, etc.)
* Display grouping
* Help text and tooltips
* Whether parameter is "advanced"
* Display order

This allows the UI to dynamically adapt to different models while maintaining a consistent user experience.

## OrderItem

An OrderItem is a request for one or more *product* to be created by a *ProductFactory*, and typically aligns to a single API request to the underlying provider.

Examples:
- A simple API call to generate an image from a provider
- A simple API call to generate a batch of images from a provider

Usage:
- One or more *OrderItems* are created from an *order* using a *base parameter set*
- A *OrderItem* can generate one or more *products*
- A *OrderItem* always has a single *order* and is performed using a single *factory*
- A *OrderItem* has a *generation parameter set* that is used by a *factory* to create an *actual parameter set* used in the API request to the provider

An OrderItem represents a specific instance of product creation with:

* Actual parameter set used (including interpolated values)
* Output parameter set (including generated values like seeds)
* Generated product reference

## Orders

An order is a request made by a user to create one or more *products* using a specific *model*, *model type* and *provider*. An order is a container for a *base parameter set* and triggers the creation of one or more *generations*.

An Order contains:

* Base parameter set (complete user input in JSON)
* Reference to the ProductFactory specification
* Project association
* Generated products

An order defines multiple generations through:

* Token expansion (e.g., [black,white] dog)
* Parameter interpolation (e.g., steps:8,10,20)
* Sub-prompt delimiters (prompt1 || prompt2)

## Order Items



## Products

Products are the individual digital outputs (E.g. images, videos, etc.) created by a generation.

Examples:
- A single image
- A single video
- A single audio file

Usage:
- One or more *products* are created from a *generation*
- A *product* may be created from a *generation*
- A *product* may also be imported from an external source
- A *product* may also be used or reference in a *base parameter set*, being specifed by a user as an input to another generation.
- A *product* has a type, such as image, video, audio, etc.

Properties:

* Type (image, video, audio)
* File information (path, size, dimensions)
* Generation reference
* Order reference
* Liked status
* Metadata

## Projects

Projects are a way to organise orders based on a specific intent, theme or concept. 

## Collections

Collections are adhoc collections of products that the user manually creates, populates and manages. 

# Smart Parameter Expansion

## Token Expansion

Square bracket tokens in prompts expand to multiple generations:

* Inline values: [red,blue,green]
* Predefined lookups: [color] expands to lookup values
* Nested lookups: lookups can reference other lookups
* Back references: [=color] references previous color value

## Parameter Interpolation

Pipeline parameters can specify multiple values:

* Comma-separated lists: steps:8,10,20
* Ranges: steps:10..20
* Random selections: steps:10|20|30

## Sub-prompts

Orders can contain multiple sub-prompts separated by || delimiter:
"A dog || A cat" creates separate generations for each

## Templates

Templates are a way to save and reuse parameter sets.


# Data Management

## Lookups

* Stored in SQLite database
* Global scope initially
* User-editable through UI
* Support for nested lookups

## Templates

* Saved as special orders in database
* Contains complete parameter sets
* Factory-scoped
* Optional project association

## Products

* File management
* Metadata storage
* Like/favorite functionality
* Generation parameter tracking

## Tags

* Cross cutting mechanism to categorise and organise projects, collections, products, etc.  



# Parameters

## ParameterSets

A parameter set is a collection of *parameters* used in the application to support the creation of a *generation*.

A parameter set can have different *parameters* based on the *model*, *model type* and *provider*.

Usage:

- A *base parameter set* is assembled from the user input and stored against an *order*
- A *generation parameter set* is created from the *base parameter set* 
- A *generation parameter set* is validated by a *factory*
- A *generation parameter set* maybe combined with a model or provider specific parameter set to create an *actual parameter set*
- A *return parameter set* is created from the return values of the API and represent the parameter values that were actually used to create the *product*. This might include defaults or other values that were not specified by the user and application. 

### Implementation

A parameter set is typically implemented as a dictionary or hash. It may be stored in a database field as a JSON object or other serialised format that can have arbitrary keys and values.

Different database models may use parameter sets in different contexts as per usage. E.g. an *order* may have a *base parameter set*. A *generation* may have a *generation parameter set* and a *return parameter set*.

## ParameterSetSpecs

A parameter set spec is a specification of the parameters that are supported by a *model*, *model type* and *provider*.



# Database Models

All database models are assumed to have an ID, created_at, updated_at and deleted_at fields.

## Order

- optionally has one or more generations
- optionally has a project
- has a status field: pending, processing, underway, fulfilled, cancelled
- has a parameter set field: base parameter set

## Generation

- related to one order
- has a status field: pending, generating, complete, failed, cancelled
- has a parameter set field: generation parameter set
- has a parameter set field: actual parameter set
- has a parameter set field: return parameter set

## Product

- has an optional generation
- has a type field: image, video, audio, etc.
- has a file field: file path, url, etc.
- has a file size field: bytes, etc.
- has adhoc metadata fields: width, height, 
- may have a binary field for thumbnail, etc.


## Projects

- has a name
- has a description
- has a status: active, archived


## Collection


## Data Management

### Lookups

* Stored in database
* Global scope initially
* User-editable through UI
* Support for nested lookups

### Templates

* Saved as special orders in database
* Contains complete parameter sets
* Factory-scoped
* Optional project association

### Products

* File management
* Metadata storage
* Like/favorite functionality
* Generation parameter tracking

### Tags

* Cross cutting mechanism to categorise and organise projects, collections, products, etc.

## Database Models

All database models are assumed to have an ID, created_at, updated_at and deleted_at fields.

### Order

- optionally has one or more generations
- optionally has a project
- has a status field: pending, processing, underway, fulfilled, cancelled
- has a parameter set field: base parameter set

### Generation

- related to one order
- has a status field: pending, generating, complete, failed, cancelled
- has a parameter set field: generation parameter set
- has a parameter set field: actual parameter set
- has a parameter set field: return parameter set

### Product

- has an optional generation
- has a type field: image, video, audio, etc.
- has a file field: file path, url, etc.
- has a file size field: bytes, etc.
- has adhoc metadata fields: width, height, 
- may have a binary field for thumbnail, etc.

### Projects

- has a name
- has a description
- has a status: active, archived

### Collection

- User-defined collections of products
- Manual organization and curation

