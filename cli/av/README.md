# Avalanche CMS CLI Documentation

The Avalanche CLI manages Avalanche CMS resources via a command set.

## Commands

### User Authentication

Manages Avalanche CMS CLI user sessions.

#### av login

Initiate a user session by logging into the CMS.

```shell
av login --user <email>
```
- A password prompt appears securely after executing the command.
- If logged in, the user ID is passed to subsequent commands with --user-id, unless otherwise passed as argument.

**Example Output**

*Successful Login:*

```json
{
  "user": {
    "id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a",
    "email": "user@example.com"
  },
  "message": "Login successful."
}
```
*Failed Login:*

```json
{
  "error": {
    "message": "Login failed.",
    "email": "user@example.com"
  }
}
```

#### av user show

Displays the details of the currently logged-in user.

```shell
av user show
```

**Example Output**

*User is Logged In:*
```json
{
  "user": {
    "id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a",
    "email": "user@example.com",
  },
  "message": "User is logged in.",
}
```

*No User Logged In:*
```json
{
  "error": {
    "message": "No user is logged in.",
  }
}
```

#### av logout

Terminates the current user session.

```shell
av logout
```

**Example Output**

*Logout Success:*

```shell
{
  "message": "User successfully logged out.",
  "user_id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a"
}
```

### Collection Management

Handles the lifecycle of collections.

#### av collection create

Creates a new collection with a specified name.

```shell
av collection create --name <name> [--user-id <id>]
```

**Example Output**

*Collection created:*

```json
{
  "collection": {
    "id": "139617dd-e0f8-4df4-811e-c643c6c50723",
    "name": "MyCollection",
    "user_id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a",
    "created_at": "2023-03-01T12:00:00Z"
  },
  "message": "Collection created successfully."
}
```

#### av collection delete

Removes an existing collection.

```shell
av collection delete --id <id> [--user-id <id>]
```

**Example Output**

*Collection deleted:*

```json
{
  "collection": {
    "id": "139617dd-e0f8-4df4-811e-c643c6c50723",
    "user_id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a",
    "deleted_at": "2023-03-01T12:00:00Z"
  },
  "message": "Collection deleted successfully."
}
```

*Collection does not exist:*

```json
{
  "error": {
    "message": "Collection does not exist.",
    "collection": {
      "id": "139617dd-e0f8-4df4-811e-c643c6c50723",
      "user_id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a"
    }
  }
}
```

#### av collection exists

Checks whether a collection exists.

```shell
av collection exists [--id <id>] [--name <name>] [--user-id <id>]
```

- Either --id <id> or --name <name> must be provided.
- If using --name, existence may refer to multiple collections, which will lead to matches > 1 in the response.

**Example Output**

*Collection Exists by ID:*
```json
{
  "exists": true,
  "message": "A collection with the specified ID exists."
}
```

*Collection Exists by Name (Single Match):*

```json
{
  "exists": true,
  "matches": 1,
  "message": "A collection with the specified name exists."
}
```

*Collection Exists by Name (Multiple Matches):*

```json
{
  "exists": true,
  "count": 2,
  "message": "Multiple collections with the specified name exist."
}
```

*No Collection Found:*

```json
{
  "exists": false,
  "message": "No collection found."
}
```

#### av collection list

Lists all collections of a user.

```shell
av collection list [--user-id <id>]
```

**Example Output**

*No collections exist:*

```json
{
  "collections": [],
  "user_id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a",
  "message": "No collections found."
}
```

*Collections found:*

```json
{
  "collections": [
    {
      "id": "139617dd-e0f8-4df4-811e-c643c6c50723",
      "name": "MyCollection",
      "created_at": "2023-03-01T12:00:00Z"
    },
    {
      "id": "3e336cdd-3087-4252-beaa-605359fbd715",
      "name": "MyCollection2",
      "created_at": "2023-03-02T12:00:00Z"
    }
  ],
  "user_id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a",
  "message": "Collections found."
}
```

#### av collection show

Displays information of a specific collection.

```shell
av collection show --id <id> [--user-id <id>]
```

**Example Output**

*Collection found:*

```json
{
  "collection": {
    "id": "139617dd-e0f8-4df4-811e-c643c6c50723",
    "name": "MyCollection",
    "user_id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a",
    "created_at": "2023-03-01T12:00:00Z"
  },
  "message": "Collection found."
}
```

#### av collection update

Updates specified fields of a collection.

```shell
av collection update --id <id> [--user-id <id>] [--name <newName>]
```

**Example Output**

*Collection Updated with Name Change:*
```json
{
  "collection": {
    "id": "139617dd-e0f8-4df4-811e-c643c6c50723",
    "name": "NewCollectionName",
    "user_id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a"
  },
  "updated_fields": ["name"],
  "message": "Collection has been updated."
}
```
*If No Fields are Specified for Update:*
```json
{
  "error": {
    "message": "No update fields provided.",
    "collection": {
      "id": "139617dd-e0f8-4df4-811e-c643c6c50723",
      "user_id": "e8da69ad-d824-4bc5-8ee1-51443489ec5a"
    },
    "updated_fields": []
  }
}
```