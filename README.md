# Team-09 0xDSSS

## Members
1. Aditya **D**utt
1. Kartikey **S**ubramanium
1. Meetesh **S**aini
1. Kushal **S**ultania

## About the project

1. The project aims to achieve fully digital cooperative bank with some novelty features like holding elections for board members, participating in elections without bias, loan approval using Machine Learning model.  

## Setup instructions
1. Clone this repo

    ```bash
    git clone https://github.com/Krypthon-Hackathon-VITC/Team-09
    ```

1. Create virtual environment
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

1. Install dependencies and frameworks
    ```bash
    pip install -r requirements.txt
    cd backend
    ```

1. Create `.env` file with environment variables
    ```
    FLASK_APP=run.py
    FLASK_ENV=development
    MONGO_URI=<URI>
    MODEL_PATH=<MODEL-PATH>
    ```

1. Run flask server using
    ```
    bash 
    cd backend
    python3 run.py
    ```

## Training the model

1. Add the dataset path in `new_model.py`
    ```
    url = "<Dataset url or path>"
    ```

1. Run `new_model.py`, it generates the trained model file `MODEL.pkl` 
    ```
    python3 new_model.py
    ```