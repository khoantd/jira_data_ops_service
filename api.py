import zipfile
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List, Optional
import logging
from pathlib import Path

from pydantic import BaseModel
from common.jira_util import export_issues_to_csv, count_issues_in_project
import db_import
from main import QueryConfig
import psycopg2
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="JIRA Query API")

# JWT Configuration
# Store this securely in environment variables
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "Admin@123")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Database connection
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'fecops'),
    'user': os.getenv('DB_USER', 'fecops-admin'),
    'password': os.getenv('DB_PASSWORD', 'fecops-admin'),
    'host': os.getenv('DB_HOST', 'khoadue.me'),
    'port': os.getenv('DB_PORT', '5434')
}

# Add these lines
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Admin@123')  # Replace in production
ADMIN_PASSWORD_HASH = pwd_context.hash(ADMIN_PASSWORD)


class QueryRequest(BaseModel):
    jql_query: str
    fields: Optional[List[str]] = None
    batch_size: Optional[int] = 1000
    filename: Optional[str] = None


class QueryResponse(BaseModel):
    total_issues: int
    total_records: int
    total_pages: int
    exported_files: List[str]


class DownloadRequest(BaseModel):
    file_names: List[str]


class ImportRequest(BaseModel):
    file_name: str


class UserCreationRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    admin_flag: Optional[bool] = False
    is_admin: Optional[bool] = False

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_admin: Optional[bool] = False

class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


# Authentication helper functions
def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return UserInDB(
            username=user[1],
            email=user[2],
            full_name=user[3],
            disabled=user[4],
            hashed_password=user[5]
        )


def authenticate_user(username: str, password: str):
    logger.info(f"Authenticating user: {username}")
    user = get_user(username)
    if not user:
        logger.info(f"Authentication failed for user: {username} - user not found")
        return False
    if not verify_password(password, user.hashed_password):
        logger.info(f"Authentication failed for user: {username} - incorrect password")
        return False
    logger.info(f"User {username} authenticated successfully")
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    logger.info("get_current_user called.")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info("Token decoded successfully.")
        
        username = payload.get("sub")
        logger.info(f"Extracted username from token: {username}")
        if username is None:
            logger.info("Username not found in token payload.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Check token expiration
        exp = payload.get("exp")
        logger.info(f"Token expiration time from payload: {exp}")
        if exp is None:
            logger.info("Expiration time not found in token payload.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if datetime.fromtimestamp(exp) < datetime.utcnow():
            logger.info("Token has expired based on current time.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Special handling for default admin user
        if username == "admin":
            logger.info("Admin user authenticated.")
            return User(
                username="admin",
                email=None,
                full_name="System Admin",
                is_admin=True  # Always set admin user as admin
            )

        # For other users, get from database
        user = get_user(username)
        if user is None:
            logger.info(f"User '{username}' not found in database.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.info(f"User '{username}' retrieved successfully.")
        return User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_admin=payload.get("is_admin", False)  # Use is_admin from token payload
        )

    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error in token validation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication",
        )


# New endpoints for user management
@app.post("/api/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # Allow admin user to authenticate
        if form_data.username == "admin":
            if verify_password(form_data.password, ADMIN_PASSWORD_HASH):
                access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                access_token = create_access_token(
                    data={"sub": "admin", "is_admin": True},  # Include admin flag
                    expires_delta=access_token_expires
                )
                return {
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
                }

        # Regular user authentication
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "is_admin": getattr(user, 'is_admin', False)},
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post("/api/users", response_model=User)
async def create_user(
    request: UserCreationRequest,
    current_user: User = Depends(get_current_user)
):
    try:
        # Log the attempt to create a user with the provided username and admin flag
        logger.info("create_user called with username: %s, admin_flag: %s", request.username, request.is_admin)
        
        # Check if the user is trying to create an admin account and verify if the current user has admin privileges
        if request.admin_flag and not getattr(current_user, 'is_admin', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can create admin accounts"
            )
        
        # Validate that the username is provided and meets the minimum length requirement
        if not request.username or len(request.username) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username must be at least 3 characters long"
            )
        
        # Validate that the password is provided and meets the minimum length requirement
        if not request.password or len(request.password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )

        # Establish a connection to the database
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Check if the username already exists in the database
                cur.execute("SELECT username FROM users WHERE username = %s", (request.username,))
                if cur.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Username already exists"
                    )

                # Hash the provided password for secure storage
                hashed_password = get_password_hash(request.password)
                
                # Insert the new user into the database and return the relevant user information
                cur.execute(
                    """
                    INSERT INTO users (username, email, full_name, disabled, hashed_password, is_admin)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING username, email, full_name
                    """,
                    (
                        request.username,
                        request.email,
                        request.full_name,
                        False,  # New users are not disabled by default
                        hashed_password,
                        request.admin_flag
                    )
                )
                user_data = cur.fetchone()
                # Commit the transaction to save changes
                conn.commit()
                
                # Return the created user's information
                return User(
                    username=user_data[0],
                    email=user_data[1],
                    full_name=user_data[2],
                    is_admin=request.admin_flag
                )

    except HTTPException as he:
        # Log and re-raise HTTP exceptions to preserve their status codes and messages
        logger.warning(f"HTTP error during user creation: {he.detail}")
        raise

    except psycopg2.Error as e:
        # Log database-related errors and raise a 500 Internal Server Error
        logger.error(f"Database error while creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )

    except Exception as e:
        # Log unexpected errors and raise a 500 Internal Server Error
        logger.error(f"Unexpected error while creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@app.post("/api/query", response_model=QueryResponse)
async def execute_query(
    query_request: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Execute a custom JQL query and export results to CSV files
    """
    try:
        config = QueryConfig()
        config.ensure_directories()

        # Use default fields if none provided
        fields = query_request.fields or config.FIELDS
        batch_size = query_request.batch_size or config.EXPORT_BATCH_SIZE

        # Use provided filename or default to 'custom_query'
        print(query_request.dict())
        base_filename = query_request.dict().get('filename', 'custom_query')
        # Ensure the base_filename does not end with '.csv' to prevent duplicate extensions
        if base_filename.lower().endswith('.csv'):
            base_filename = base_filename[:-4]

        # Get query statistics
        result = count_issues_in_project(
            query_request.jql_query,
            str(config.CONFIG_FILE)
        )

        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to get issue count from JIRA"
            )

        total, records, pages = result

        if records == 0:
            return QueryResponse(
                total_issues=0,
                total_records=0,
                total_pages=0,
                exported_files=[]
            )

        exported_files = []
        # Export tickets in batches
        for batch in range(0, records, batch_size):
            # Delete existing CSV files with the same base filename
            for existing_file in config.DATA_DIR.glob(f'{base_filename.lower()}*.csv'):
                try:
                    existing_file.unlink()
                    logger.info(f"Deleted existing file: {existing_file}")
                except Exception as e:
                    logger.warning(f"Failed to delete file {existing_file}: {str(e)}")
            output_file = config.DATA_DIR / \
                f'{base_filename}_batch_{batch // batch_size + 1}.csv'

            success, count = export_issues_to_csv(
                query_request.jql_query,
                str(config.CONFIG_FILE),
                fields,
                str(output_file),
                max_results=batch_size,
                start_at=batch
            )

            if not success:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to export batch starting at {batch}"
                )

            exported_files.append(str(output_file))
            logger.info(f"Exported {count:,} tickets to {output_file}")

        return QueryResponse(
            total_issues=total,
            total_records=records,
            total_pages=pages,
            exported_files=exported_files
        )

    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/download-csv")
async def download_csv(
    request: DownloadRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint to download specified CSV files as a zip archive or individual CSV file.

        Args:
            request (DownloadRequest): Request body containing list of file names to download.

        Returns:
            FileResponse: Zip archive containing the requested CSV files or individual CSV file.
    """
    try:
        data_dir = db_import.Config.DATA_DIR
        # Validate requested files
        missing_files = [
            f for f in request.file_names if not (data_dir / f).exists()
        ]
        if missing_files:
            raise HTTPException(
                status_code=404,
                detail=f"Files not found: {', '.join(missing_files)}"
            )

        if len(request.file_names) == 1:
            # Return individual CSV file
            file_name = request.file_names[0]
            file_path = data_dir / file_name
            return FileResponse(
                path=file_path,
                media_type='text/csv',
                filename=file_name
            )
        else:
            # Create a zip archive of the requested files
            zip_filename = "requested_files.zip"
            zip_path = data_dir / zip_filename
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for file_name in request.file_names:
                    file_path = data_dir / file_name
                    zipf.write(file_path, arcname=file_name)

            return FileResponse(
                path=zip_path,
                media_type='application/zip',
                filename=zip_filename
            )
    except Exception as e:
        logger.error(f"Error downloading CSV files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/download-binary-csv")
async def download_binary_csv(
    request: DownloadRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint to download specified CSV files as binary data.

        Args:
            request (DownloadRequest): Request body containing list of file names to download.

        Returns:
            Response: Binary data of CSV file or zip archive containing the requested CSV files.
    """
    try:
        data_dir = db_import.Config.DATA_DIR
        # Validate requested files
        missing_files = [
            f for f in request.file_names if not (data_dir / f).exists()
        ]
        if missing_files:
            raise HTTPException(
                status_code=404,
                detail=f"Files not found: {', '.join(missing_files)}"
            )

        if len(request.file_names) == 1:
            # Return individual CSV file as binary
            file_name = request.file_names[0]
            file_path = data_dir / file_name
            with open(file_path, 'rb') as f:
                binary_data = f.read()
            return Response(
                content=binary_data,
                media_type='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename="{file_name}"'
                }
            )
        else:
            # Create a zip archive in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_name in request.file_names:
                    file_path = data_dir / file_name
                    with open(file_path, 'rb') as f:
                        zipf.writestr(file_name, f.read())
            
            return Response(
                content=zip_buffer.getvalue(),
                media_type='application/zip',
                headers={
                    'Content-Disposition': 'attachment; filename="requested_files.zip"'
                }
            )
    except Exception as e:
        logger.error(f"Error downloading CSV files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/import-data")
async def import_data_task(
    request: ImportRequest,
    current_user: User = Depends(get_current_user)
):
    """Endpoint to execute data import task with specified file name"""
    try:
        file_name = request.file_name

        # Execute import and handle dictionary return value
        result = db_import.execute_import(file_name)
        if result is None:
            raise HTTPException(
                status_code=500,
                detail="Import operation failed with no return value"
            )

        # Handle dictionary return format
        if not isinstance(result, dict):
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected return format from import operation: {result}"
            )

        logger.info(
            f"Data import task completed successfully for file: {file_name}")
        return {
            "status": "success",
            "message": f"Successfully imported {result['total_imported_data']} records",
            "details": result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error executing data import task for file {file_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

def init_db():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(100) UNIQUE NOT NULL,
                        email VARCHAR(100),
                        full_name VARCHAR(100),
                        disabled BOOLEAN DEFAULT FALSE,
                        hashed_password VARCHAR(255) NOT NULL,
                        is_admin BOOLEAN DEFAULT FALSE,
                        admin_flag BOOLEAN DEFAULT FALSE
                    )
                """)
                conn.commit()
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        raise

# Call this when your application starts
init_db()