@echo off
set PYTHONUTF8=1
echo ========================================================
echo Running Resolution Predictor Pipeline
echo ========================================================

echo.
echo [1/4] Cleaning raw data...
python src\clean_data.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo [2/4] Splitting data into train/val/test...
python src\split_data.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo [3/4] Training XGBoost model (Phases 1-3)...
python src\train_model.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo [4/4] Evaluating final model on test set...
python src\evaluate_test.py
if %errorlevel% neq 0 exit /b %errorlevel%

echo.
echo ========================================================
echo Pipeline completed successfully! Models are in 'models/'
echo You can test predictions using: python src\predict.py
echo ========================================================
pause
