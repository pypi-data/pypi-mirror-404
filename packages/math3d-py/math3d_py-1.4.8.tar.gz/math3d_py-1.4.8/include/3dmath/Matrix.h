#pragma once
#include <ostream>
#include <string>
#include <initializer_list>
#include <exception>
#include <memory>
#include <sstream>
#include <iomanip>
#include <filesystem>
#include "Vector.h"

namespace math3d {

// A column-major matrix that stores its elements in contiguous memory

// By default, the implementation assumes that the input data passed to it
// is in row major order. Allowing the client to use row-major order allows
// the client to lay out columns of their column-major matrices as columns.
// For example,
// auto myMatrix = Matrix<float, 4, 4> {
// {a, e, i, m},
// {b, f, j, n},
// {c, g, k, o},
// {d, h, l, p}};
// If the code assumed column-major then this matrix in code would be
// transposed and could cause misinterpretation.
//
// The order of the input can be controlled by using the constructor
// argument Order.
enum class Order {
    ColumnMajor,
    RowMajor
};

template<typename DataType, unsigned numRows, unsigned numCols>
class Matrix {

    static_assert(std::is_integral_v<DataType> ||
        std::is_floating_point_v<DataType>, "Matrix elements should be of fundamental type");
    
    public:

        // Default construction. Elements of the new matrix will be zero-initialized
        Matrix() : data(std::make_unique<DataType[]>(numRows * numCols)) {
        }
        
        // Construction via an initializer list of initializer lists 
        // Each sub-initializer defines a column or row of matrix data.
        // The enum Order argument specifies the format of the data. 
        // If the order is column major, then each sub-initializer is
        // treated as a column of data otherwise the data is assumed
        // to be in the row major order
        Matrix(std::initializer_list<std::initializer_list<DataType>> const& initList, Order const& order = Order::RowMajor) {
            
            // allocate memory
            data = std::make_unique<DataType[]>(numRows * numCols);
            
            // read and store data in data as per the format of the input data
            order == Order::ColumnMajor ? readColumnMajor(initList) : readRowMajor(initList);
        }

        explicit Matrix(std::vector<std::vector<DataType>> const& input, Order const& order = Order::RowMajor) {
            // allocate memory
            data = std::make_unique<DataType[]>(numRows * numCols);

            // read and store data in data as per the format of the input data
            order == Order::ColumnMajor ? readColumnMajor(input) : readRowMajor(input);
        }

        // Construct with data from a 1D vector. This is useful to build minors and cofactors
        explicit Matrix(std::vector<DataType> const& inputData, Order const& order = Order::RowMajor) {
            // allocate memory
            data = std::make_unique<DataType[]>(numRows * numCols);
            for (int i = 0; i < numRows; ++i) {
                for (int j = 0; j < numCols; ++j) {
                    data[i * numRows + j] =
                            order == Order::ColumnMajor ?
                            inputData[i * numRows + j] : inputData[j * numCols + i];
                }
            }
        }
        
        // Copy construction 
        Matrix(Matrix const& other) {
            assign(other);
        }
        
        // Copy assignment
        Matrix& operator=(Matrix const& other) {
            assign(other);
            return *this;
        }

        // Move construction
        Matrix(Matrix&& other)  noexcept {
            data = std::move(other.data);
        }
        
        // Move assignment
        Matrix& operator=(Matrix&& other)  noexcept {
            data = std::move(other.data);
            return *this;
        }
        
        // Destructor 
        ~Matrix()  = default;

        // Conversion operator to get the data as const pointer. Useful for calling OpenGL functions that expect a
        // pointer with a matrix argument instead and have the matrix converted implicitly to a pointer
        operator DataType const*() { // NOLINT: Implicit conversion is the point of defining this operator
            return data.get();
        }

        // Vector multiplication
        [[nodiscard]]
        auto operator*(Vector<DataType, numRows> const& inputVector) const {
            Vector<DataType, numRows> outputVector;
            for (auto row = 0u; row < numRows; ++row) {
                for (auto col = 0u; col < numCols; ++col) {
                    outputVector[row] += data[col * numRows + row] * inputVector[col];
                }
            }
            return outputVector;
        }

        // Matrix multiplication
        template<typename T, unsigned multiplierNumRows, unsigned multiplierNumCols>
        [[nodiscard]]
        auto operator*(Matrix<T, multiplierNumRows, multiplierNumCols> const& another) const {
            static_assert(std::is_same<DataType, T>::value, "Matrix data types should be compatible");
            static_assert(numCols == multiplierNumRows, "Matrix dimensions are not compatible");
            Matrix<T, numRows, multiplierNumCols> result;
            T* resultData = const_cast<T*>(result.operator const DataType *());
            for (auto row = 0u; row < numRows; ++row) {
                auto rowVector = this->operator()(row);
                for (auto col = 0u; col < multiplierNumCols; ++col) {
                    Vector<DataType, multiplierNumRows> columnVector = another[col];
                    resultData[col * multiplierNumCols + row] = rowVector.dot(columnVector);
                }
            }
            return result;
        }

        [[nodiscard]]
        unsigned getNumberOfRows() const { //NOLINT: Ignore static member function suggestion
            return numRows;
        }

        [[nodiscard]]
        unsigned getNumberOfColumns() const { //NOLINT: Ignore static member function suggestion
            return numCols;
        }

        [[nodiscard]]
        const DataType* getData() const {
            return data.get();
        }

        // const version of conversion operator to get the data as const pointer
        [[nodiscard]]
        operator const DataType*() const { // NOLINT: Conversion to pointer is the purpose of this method
            return data.get();
        }

        // Column access
        Vector<DataType, numRows> operator[](unsigned const index) const {
            if (index >= numCols) {
                throw std::runtime_error(
                        "Matrix::operator[]() : Invalid access. " + std::to_string(index) + " is not a valid column"
                        " index for a " + std::to_string(numRows) + 'x' + std::to_string(numCols) + " matrix");
            }
            Vector<DataType, numRows> result;
            for (unsigned i = 0; i < numRows; ++i) {
                result[i] = data[index * numRows + i];
            }
            return result;
        }

        // Row access
        Vector<DataType, numCols> operator()(unsigned const rowIndex) const {
            Vector<DataType, numCols> result;
            for (unsigned i = 0, index = rowIndex; i < numCols; ++i, index += numRows) {
                result[i] = data[index];
            }
            return result;
        }

        // These two operators allow assignment expression of the form
        // matrix[i] = columnVector
        Matrix& operator[](unsigned const index) {
            if (currentColumn != -1) {
                throw std::runtime_error(
                        "Matrix::operator[]() : Invalid access. Previous column access operation is still in progress");
            }
            if (index >= numCols) {
                throw std::runtime_error(
                        "Matrix::operator[]() : Invalid access. " + std::to_string(index) + " is not a valid column"
                        " index for a " + std::to_string(numRows) + 'x' + std::to_string(numCols) + " matrix");
            }
            currentColumn = index;
            return *this;
        }

        void operator=(Vector<DataType, numCols> const& vector) { // NOLINT: Specific use case to assign columns to matrix
            if(currentColumn == -1) {
                throw std::runtime_error("Invalid assignment. Check assignment expressions");
            }
            memcpy(data.get() + currentColumn * numCols, vector.getData(), numCols * sizeof(DataType));
            currentColumn = -1;
        }

        // Conversion to vector
        // Allows expression of the form Vector<DataType, numRows> column0 = Matrix[0]
        operator Vector<DataType, numRows>() const { // NOLINT: Specific use case to assign columns to matrix
            if(currentColumn == -1) {
                throw std::runtime_error("Invalid conversion to vector. Check assignment expressions");
            }
            Vector<DataType, numRows> result;
            for (unsigned i = 0, index = currentColumn * numRows; i < numRows; ++i) {
                result[i] = data[index+i];
            }
            currentColumn = -1;
            return result;
        }

        // Element access operators to allow assignment of individual elements in the form of expression
        // matrix(a, b) = c
        Matrix& operator()(unsigned const rowIndex, unsigned const columnIndex) {
            validateElementAccess(rowIndex, columnIndex);
            currentColumn = columnIndex;
            currentRow = rowIndex;
            return *this;
        }

        void operator=(DataType value) { //NOLINT: Specific for element assignment
            if (currentColumn != -1 && currentRow != -1) {
                data[currentColumn * numRows + currentRow] = value;
                currentColumn = -1;
                currentRow = -1;
            } else {
                throw std::runtime_error("Invalid assignment. Check assignment expressions");
            }
        }

        // Conversion operator that allows extraction of the current element
        // This allows "matrix(a, b)" to appear in non-assignment contexts
        // float xyz = matrix(a, b);
        // or
        // ASSERT_EQ(matrix(a,b), someScalar)
        // NOTE: Matrix& Matrix::operator(row, column) will be resolved in assignment expressions
        operator DataType() const { // NOLINT: Specific for element access
            DataType scalar;
            if (currentColumn != -1 && currentRow != -1) {
                scalar = data[currentColumn * numRows + currentRow];
                currentColumn = -1;
                currentRow = -1;
            } else {
                throw std::runtime_error("Invalid conversion. Check element access expressions");
            }
            return scalar;
        }

        // Element access for const objects
        DataType operator()(unsigned const rowIndex, unsigned const columnIndex) const {
            validateElementAccess(rowIndex, columnIndex);
            return data[columnIndex * numRows + rowIndex];
        }

        // Extract a range of elements into a new matrix
        template<unsigned newNumRows, unsigned newNumCols>
        Matrix<DataType, newNumRows, newNumCols> extract(unsigned const startingRow = 0, unsigned const startingColumn = 0) {
           if (startingRow >= numRows || startingColumn >= numCols) {
               throw std::runtime_error(
                   "Matrix::extract() [" + std::to_string(startingRow) + ',' + std::to_string(startingColumn) + ']' +
                   "is not a valid range for a " + std::to_string(numRows) + 'x' + std::to_string(numCols) + "matrix");
           }
           Matrix<DataType, newNumRows, newNumCols> extractedMatrix;
           DataType* extractedMatrixData = const_cast<DataType*>(extractedMatrix.getData());
           unsigned newMatrixElementIndex = 0;
           for (unsigned j = startingColumn; j < startingColumn + newNumCols; ++j) {
               for (unsigned i = startingRow; i < startingRow + newNumRows; ++i) {
                   extractedMatrixData[newMatrixElementIndex++] = data[j * numRows + i];
               }
           }
           return extractedMatrix;
        }

        // Print column major matrix data in row order format
        void print(std::ostream& os, float zero = 1e-3) const {
            for (unsigned row = 0; row < numRows; ++row) {
                for (unsigned col = 0; col < numCols; ++col) {
                    auto val = data[col * numRows + row];
                    if (fabs(val) <= zero) {
                        val = 0;
                    }
                    os << std::setw(10) << std::setprecision(6) << val;
                    if (col != numCols - 1) os << ' ';
                }
                os << std::endl;
            }
        }

        void print() const {
            print(std::cout);
        }

        [[nodiscard]]
        std::string asString() const {
            std::stringstream stringStream;
            print(stringStream);
            return stringStream.str();
        }

        // Defined in MatrixOperations.h
        Matrix transpose();
        DataType determinant();
        Matrix inverse();
        unsigned convertToUpperTriangular(Matrix& upperTriangular) const;
        void swapRows(unsigned rowA, unsigned rowB);
        void addRow(unsigned rowIndex, Vector<DataType, numCols> const& anotherRow);
        void subtractRow(unsigned rowIndex, Vector<DataType, numCols> const& anotherRow);

        // Defined in MatrixUtil.h
        static void readFromFile(std::filesystem::path const& matrixFile, Matrix&, char delimiter = ',');

protected:
        std::unique_ptr<DataType[]> data;
        mutable int currentColumn {-1};
        mutable int currentRow {-1};


    private:
        static void validateElementAccess(unsigned const rowIndex, unsigned const columnIndex) {
            auto const badRowIndex = rowIndex >= numRows;
            auto const badColumnIndex = columnIndex >= numCols;
            if (badRowIndex || badColumnIndex) {
                std::stringstream errorMessage;
                errorMessage << "Invalid access: ";
                if (badRowIndex) {
                    errorMessage << rowIndex << " is not a valid row index";
                    errorMessage << " for a " << numRows << 'x' << numCols << " matrix" << std::endl;
                }
                if (badColumnIndex) {
                    errorMessage << columnIndex << " is not a valid column index";
                    errorMessage << " for a " << numRows << 'x' << numCols << " matrix" << std::endl;
                }
                throw std::runtime_error(errorMessage.str());
            }
        }

        void assign(Matrix const& other) {
            if (this != &other) {
                data = std::make_unique<DataType[]>(numRows * numCols);
                for (unsigned col = 0; col < numCols; ++col) {
                    for (unsigned row = 0; row < numRows; ++row) {
                        auto index = col * numRows + row;
                        data[index] = other.data[index];
                    }
                }
            }
        }
        
        void readColumnMajor(auto const& initList) {

            // Number of columns in input data should match numCols 
            if (numCols != initList.size()) {
                throw std::invalid_argument(
                        std::string("Incompatible dimensions: Matrix dimensions are [" + 
                                    std::to_string(numRows) + ',' + std::to_string(numCols) + "] " +
                                    "Number of columns in the input is " + std::to_string(initList.size())));
            }
            
            // Number of rows for each column of the input data should match numRows 
            for (unsigned col = 0; col < numCols; ++col) {
                if (std::data(initList)[col].size() != numRows) {
                    throw std::invalid_argument(
                        std::string("Incompatible dimensions: Matrix dimensions are [" + 
                                    std::to_string(numRows) + ',' + std::to_string(numCols) + "] " +
                                    "Number of rows in column " + std::to_string(col+1) + 
                                    " is " + std::to_string(std::data(initList)[col].size())));
                }
            }
            
            // Read and store data in column major format 
            for (unsigned col = 0; col < numCols; ++col) {
                for (unsigned row = 0; row < numRows; ++row) {
                    data[col * numRows + row] = std::data(std::data(initList)[col])[row];
                }
            }
        }
        
        void readRowMajor(auto const& initList) {

            // Number of rows in input data should match numRows 
            if (numRows != initList.size()) {
                throw std::invalid_argument(
                        std::string("Incompatible dimensions: Matrix dimensions are [" + 
                                    std::to_string(numRows) + ',' + std::to_string(numCols) + "] " +
                                    "Number of rows in the input is " + std::to_string(initList.size())));
            }
            
            // Number of columns in each row of the input data should match numCols 
            for (unsigned row = 0; row < numRows; ++row) {
                if (std::data(initList)[row].size() != numCols) {
                    throw std::invalid_argument(
                        std::string("Incompatible dimensions: Matrix dimensions are [" + 
                                    std::to_string(numRows) + ',' + std::to_string(numCols) + "] " +
                                    "Number of columns in row " + std::to_string(row+1) + 
                                    " is " + std::to_string(std::data(initList)[row].size())));
                }
            }

            // Read row major data and store in column major format 
            for (unsigned col = 0; col < numCols; ++col) {
                for (unsigned row = 0; row < numRows; ++row) {
                    data[col * numRows + row] = std::data(std::data(initList)[row])[col];
                }
            }
        }

        template<typename T, unsigned, unsigned>
        friend class MatrixTestWrapper;

        // Allow primary matrices to access private data of augmented matrices
        friend class Matrix<DataType, numRows, numCols/2>;
        friend class Matrix<DataType, numRows, numCols-1>;
};

template<typename DataType, size_t numRows, size_t numCols>
class AugmentedMatrix : public Matrix<DataType, numRows, numCols> {
    using BaseClass = Matrix<DataType, numRows, numCols>;

    public:
        // Create an augmented matrix by concatenating the primary matrix and secondary matrices
        template<unsigned numPrimaryColumns>
        AugmentedMatrix(Matrix<DataType, numRows, numPrimaryColumns> const& primaryMatrix,
                        Matrix<DataType, numRows, numCols-numPrimaryColumns> const& secondaryMatrix) {
            DataType const* primaryMatrixData = primaryMatrix;
            memcpy(BaseClass::data.get(), primaryMatrixData, sizeof(DataType) * (numRows * numPrimaryColumns));
            DataType const* secondaryMatrixData = secondaryMatrix;
            for (unsigned col = numPrimaryColumns; col < numCols; ++col) {
                for (unsigned row = 0; row < numRows; ++row) {
                    BaseClass::data[col * numRows + row] = secondaryMatrixData[(col - numPrimaryColumns) * numRows + row];
                }
            }
        }

        // Create an augmented matrix by concatenating the primary matrix and a vector
        template<unsigned numPrimaryColumns>
        AugmentedMatrix(Matrix<DataType, numRows, numPrimaryColumns> const& primaryMatrix,
                        Vector<DataType, numRows> const& secondaryVector) {
            DataType const* primaryMatrixData = primaryMatrix;
            memcpy(BaseClass::data.get(), primaryMatrixData, sizeof(DataType) * (numRows * numPrimaryColumns));
            for (unsigned row = 0; row < numRows; ++row) {
                BaseClass::data[numPrimaryColumns * numRows + row] = secondaryVector[row];
            }
        }
};

template<typename DataType, unsigned numRows, unsigned numCols>
inline std::ostream& operator<<(std::ostream& os, const Matrix<DataType, numRows, numCols>& m) { // NOLINT: clang-tidy is being greedy.
                                                                                                  // Non-member templates have to be inline to avoid ODR violations
    m.print(os);
    return os;
}

}
