# Lesson 6: Result Validation with Pydantic

## Overview

One of PydanticAI's most powerful features is structured output validation using Pydantic models. In this lesson, you'll learn:
- How to specify result types with Pydantic models
- Automatic validation of agent outputs
- Handling validation errors
- Complex nested structures
- Best practices for structured outputs

## Why Validated Outputs?

Instead of getting plain text responses, you can get:
- **Type-safe data**: Guaranteed correct types
- **Validated data**: Constraints and business rules enforced
- **Structured data**: Easy to work with programmatically
- **Documented schema**: Clear data contracts

## Basic Result Types

### Simple Type Validation

Specify a result type when creating the agent:

```python
from pydantic_ai import Agent

# Agent that returns a boolean
agent = Agent(
    'openai:gpt-4',
    result_type=bool
)

result = agent.run_sync('Is Python a programming language?')
print(result.data)  # True (as a boolean, not string)
print(type(result.data))  # <class 'bool'>
```

### Built-in Types

```python
from pydantic_ai import Agent

# Integer result
int_agent = Agent('openai:gpt-4', result_type=int)
result = int_agent.run_sync('What is 5 + 3?')
print(result.data)  # 8

# Float result
float_agent = Agent('openai:gpt-4', result_type=float)
result = float_agent.run_sync('What is pi to 2 decimal places?')
print(result.data)  # 3.14

# List result
list_agent = Agent('openai:gpt-4', result_type=list[str])
result = list_agent.run_sync('List 3 programming languages')
print(result.data)  # ['Python', 'JavaScript', 'Java']
```

## Pydantic Models

### Simple Model

Define a Pydantic model for structured output:

```python
from pydantic_ai import Agent
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    email: str

agent = Agent(
    'openai:gpt-4',
    result_type=Person,
    system_prompt='Extract person information from the text.'
)

result = agent.run_sync(
    'John Doe is 30 years old and his email is john@example.com'
)

print(result.data.name)   # 'John Doe'
print(result.data.age)    # 30
print(result.data.email)  # 'john@example.com'
print(type(result.data))  # <class 'Person'>
```

### Model with Validation

Add validators to ensure data quality:

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class Product(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    price: float = Field(..., gt=0, description='Price must be positive')
    category: Literal['electronics', 'clothing', 'food', 'other']
    in_stock: bool
    quantity: int = Field(..., ge=0, description='Quantity cannot be negative')
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        # Capitalize first letter of each word
        return v.title()

agent = Agent(
    'openai:gpt-4',
    result_type=Product,
    system_prompt='Extract product information and structure it properly.'
)

result = agent.run_sync(
    'The laptop pro costs $999.99, is in the electronics category, '
    'currently in stock with 15 units available'
)

print(result.data.name)      # 'Laptop Pro'
print(result.data.price)     # 999.99
print(result.data.category)  # 'electronics'
print(result.data.in_stock)  # True
print(result.data.quantity)  # 15
```

## Complex Nested Structures

### Nested Models

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import List
from datetime import date

class Address(BaseModel):
    street: str
    city: str
    country: str
    postal_code: str

class OrderItem(BaseModel):
    product_name: str
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)

class Order(BaseModel):
    order_id: str
    customer_name: str
    delivery_address: Address
    items: List[OrderItem]
    order_date: date
    total_amount: float

agent = Agent(
    'openai:gpt-4',
    result_type=Order,
    system_prompt='Extract complete order information from the text.'
)

text = """
Order #ORD-123 for Alice Smith
Delivery to: 123 Main St, New York, USA, 10001
Ordered on 2024-01-15

Items:
- Laptop: 1 unit at $999.99
- Mouse: 2 units at $29.99 each

Total: $1059.97
"""

result = agent.run_sync(text)

print(result.data.customer_name)  # 'Alice Smith'
print(result.data.delivery_address.city)  # 'New York'
print(result.data.items[0].product_name)  # 'Laptop'
print(result.data.total_amount)  # 1059.97
```

### Lists of Objects

```python
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import List

class Movie(BaseModel):
    title: str
    year: int
    director: str
    genre: str
    rating: float = Field(..., ge=0, le=10)

agent = Agent(
    'openai:gpt-4',
    result_type=List[Movie],
    system_prompt='Extract movie information and return as a list.'
)

result = agent.run_sync("""
List some classic movies:
1. The Shawshank Redemption (1994) by Frank Darabont - Drama - 9.3/10
2. The Godfather (1972) by Francis Ford Coppola - Crime - 9.2/10
3. The Dark Knight (2008) by Christopher Nolan - Action - 9.0/10
""")

for movie in result.data:
    print(f"{movie.title} ({movie.year}) - Rating: {movie.rating}")
```

## Data Extraction Use Cases

### Contact Information Extractor

```python
from pydantic_ai import Agent
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional

class ContactInfo(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[HttpUrl] = None
    company: Optional[str] = None

agent = Agent(
    'openai:gpt-4',
    result_type=ContactInfo,
    system_prompt='Extract contact information from business cards or emails.'
)

result = agent.run_sync("""
Jane Williams
Senior Software Engineer
TechCorp Inc.
Email: jane.williams@techcorp.com
Phone: +1-555-0123
Website: https://techcorp.com
""")

print(f"Name: {result.data.name}")
print(f"Company: {result.data.company}")
print(f"Email: {result.data.email}")
print(f"Website: {result.data.website}")
```

### Meeting Notes Extractor

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

class ActionItem(BaseModel):
    task: str
    assignee: str
    due_date: Optional[str] = None
    priority: Literal['low', 'medium', 'high'] = 'medium'

class MeetingNotes(BaseModel):
    meeting_title: str
    date: str
    attendees: List[str]
    key_decisions: List[str] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)
    next_meeting: Optional[str] = None

agent = Agent(
    'openai:gpt-4',
    result_type=MeetingNotes,
    system_prompt='Extract structured meeting notes from unstructured text.'
)

text = """
Product Planning Meeting - January 15, 2024

Attendees: Alice (PM), Bob (Engineer), Carol (Designer)

Decisions Made:
- Moving forward with the new dashboard design
- Will use React for the frontend
- Target launch date: March 1, 2024

Action Items:
- Alice: Create user stories by Jan 20 (HIGH priority)
- Bob: Set up development environment by Jan 18 (MEDIUM priority)
- Carol: Finalize mockups by Jan 22

Next meeting: January 22, 2024 at 2 PM
"""

result = agent.run_sync(text)

print(f"Meeting: {result.data.meeting_title}")
print(f"Attendees: {', '.join(result.data.attendees)}")
print(f"\nAction Items:")
for item in result.data.action_items:
    print(f"  - {item.assignee}: {item.task} ({item.priority})")
```

### Invoice Parser

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import List
from decimal import Decimal

class InvoiceItem(BaseModel):
    description: str
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    total: Decimal = Field(..., gt=0)

class Invoice(BaseModel):
    invoice_number: str
    invoice_date: str
    vendor_name: str
    customer_name: str
    items: List[InvoiceItem]
    subtotal: Decimal
    tax: Decimal
    total: Decimal

agent = Agent(
    'openai:gpt-4',
    result_type=Invoice,
    system_prompt='Parse invoice data and extract all relevant information.'
)

invoice_text = """
INVOICE #INV-2024-001
Date: January 15, 2024

From: TechSupply Inc.
To: Acme Corporation

Items:
1. Laptop Computer x2 @ $999.99 = $1,999.98
2. Wireless Mouse x5 @ $29.99 = $149.95
3. USB Cable x10 @ $9.99 = $99.90

Subtotal: $2,249.83
Tax (10%): $224.98
Total: $2,474.81
"""

result = agent.run_sync(invoice_text)

print(f"Invoice: {result.data.invoice_number}")
print(f"From: {result.data.vendor_name}")
print(f"To: {result.data.customer_name}")
print(f"Total: ${result.data.total}")
```

## Handling Validation Errors

### Retry on Validation Failure

PydanticAI automatically retries if the model returns invalid data:

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field

class Temperature(BaseModel):
    celsius: float = Field(..., ge=-273.15, description='Temperature in Celsius')
    fahrenheit: float = Field(..., ge=-459.67, description='Temperature in Fahrenheit')

agent = Agent(
    'openai:gpt-4',
    result_type=Temperature,
    system_prompt='Convert temperatures and ensure physical validity.',
    retries=3  # Will retry up to 3 times on validation errors
)

result = agent.run_sync('The temperature in New York is 72°F')
print(f"Celsius: {result.data.celsius}")
print(f"Fahrenheit: {result.data.fahrenheit}")
```

### Custom Validation Messages

```python
from pydantic_ai import Agent
from pydantic import BaseModel, field_validator, ValidationError

class CreditCard(BaseModel):
    card_number: str
    expiry_month: int = Field(..., ge=1, le=12)
    expiry_year: int
    cvv: str
    
    @field_validator('card_number')
    @classmethod
    def validate_card_number(cls, v: str) -> str:
        # Remove spaces and dashes
        v = v.replace(' ', '').replace('-', '')
        
        if not v.isdigit():
            raise ValueError('Card number must contain only digits')
        
        if len(v) != 16:
            raise ValueError('Card number must be 16 digits')
        
        return v
    
    @field_validator('cvv')
    @classmethod
    def validate_cvv(cls, v: str) -> str:
        if not v.isdigit() or len(v) not in [3, 4]:
            raise ValueError('CVV must be 3 or 4 digits')
        return v

agent = Agent(
    'openai:gpt-4',
    result_type=CreditCard,
    system_prompt='Extract credit card information. Be careful with formatting.'
)
```

## Optional Fields and Defaults

```python
from pydantic_ai import Agent
from pydantic import BaseModel, Field
from typing import Optional

class BookReview(BaseModel):
    title: str
    author: str
    rating: int = Field(..., ge=1, le=5, description='Rating from 1 to 5')
    review_text: str
    reviewer_name: Optional[str] = None
    recommended: bool = True
    date_reviewed: Optional[str] = None

agent = Agent(
    'openai:gpt-4',
    result_type=BookReview,
    system_prompt='Extract book review information. Some fields may be missing.'
)

result = agent.run_sync("""
"The Great Gatsby" by F. Scott Fitzgerald is a masterpiece. 
I give it 5 stars. The prose is beautiful and the story is timeless.
I highly recommend this book to everyone.
""")

print(f"Title: {result.data.title}")
print(f"Rating: {result.data.rating}/5")
print(f"Reviewer: {result.data.reviewer_name or 'Anonymous'}")
print(f"Recommended: {result.data.recommended}")
```

## Union Types

Handle multiple possible response types:

```python
from pydantic_ai import Agent
from pydantic import BaseModel
from typing import Union

class SuccessResponse(BaseModel):
    status: Literal['success']
    data: dict
    message: str

class ErrorResponse(BaseModel):
    status: Literal['error']
    error_code: str
    error_message: str

ResponseType = Union[SuccessResponse, ErrorResponse]

agent = Agent(
    'openai:gpt-4',
    result_type=ResponseType,
    system_prompt='Process the request and return either success or error response.'
)

result = agent.run_sync('Process order #12345')

if isinstance(result.data, SuccessResponse):
    print(f"Success: {result.data.message}")
elif isinstance(result.data, ErrorResponse):
    print(f"Error: {result.data.error_message}")
```

## Best Practices

### 1. Use Descriptive Field Names

```python
# ✅ Good
class User(BaseModel):
    user_id: str
    email_address: EmailStr
    registration_date: datetime

# ❌ Bad
class User(BaseModel):
    uid: str
    em: str
    dt: datetime
```

### 2. Add Field Descriptions

```python
class Product(BaseModel):
    name: str = Field(..., description='Product name as shown to customers')
    price: float = Field(..., gt=0, description='Price in USD, must be positive')
    stock: int = Field(..., ge=0, description='Number of units in stock')
```

### 3. Use Appropriate Types

```python
from pydantic import EmailStr, HttpUrl, UUID4
from datetime import datetime, date

class UserProfile(BaseModel):
    user_id: UUID4  # Not just str
    email: EmailStr  # Not just str
    website: HttpUrl  # Not just str
    birthdate: date  # Not datetime if you only need date
    created_at: datetime  # Use datetime for timestamps
```

### 4. Provide Examples

```python
class SearchQuery(BaseModel):
    """
    Search query parameters.
    
    Example:
        SearchQuery(
            query='laptop',
            category='electronics',
            max_price=1000.0,
            sort_by='price'
        )
    """
    query: str
    category: Optional[str] = None
    max_price: Optional[float] = None
    sort_by: Literal['relevance', 'price', 'rating'] = 'relevance'
```

## Exercise

Create an agent that extracts job posting information with the following structure:

```python
class JobPosting(BaseModel):
    job_title: str
    company_name: str
    location: str
    job_type: Literal['full-time', 'part-time', 'contract', 'internship']
    salary_range: Optional[str]
    requirements: List[str]
    responsibilities: List[str]
    application_deadline: Optional[str]
```

Test it with various job posting formats and ensure proper validation.

## What's Next?

In the next lesson, we'll explore:
- Streaming responses from agents
- Handling partial results
- Progress indicators
- Real-time user feedback

---

**Previous Lesson**: [Lesson 5: Tools and Function Calling](../lesson-05-tools/README.md)  
**Next Lesson**: [Lesson 7: Streaming Responses](../lesson-07-streaming/README.md)
