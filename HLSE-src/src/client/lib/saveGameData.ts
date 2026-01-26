const HEADER_B = new Uint8Array([ 71, 86, 65, 83 ]);
const PRIMARY_DB_B = new Uint8Array([ 82, 97, 119, 68, 97, 116, 97, 98, 97, 115, 101, 73, 109, 97, 103, 101 ]);
const SECONDARY_DB_B = new Uint8Array([ 82, 97, 119, 69, 120, 99, 108, 117, 115, 105, 118, 101, 73, 109, 97, 103, 101 ]);
const BYTE_HEADER = new Uint8Array([ 66, 121, 116, 101, 80, 114, 111, 112, 101, 114, 116, 121 ]);

interface DBLocation
{
    sizeOffset : number;
    dbOffset : number;
}

export class SaveGameData
{
    #saveFileBuffer : ArrayBuffer;
    #saveFileBytes : Uint8Array;
    #saveFileView : DataView;
    #primaryDBBytes : Uint8Array;
    #secondaryDBBytes : Uint8Array;
    #primaryDBLocation : DBLocation;
    #secondaryDBLocation : DBLocation;

    constructor(saveBytes : ArrayBuffer)
    {
        this.#saveFileBuffer = saveBytes;
        this.#saveFileView = new DataView(saveBytes);
        this.#saveFileBytes = new Uint8Array(this.#saveFileBuffer);

        const headerIndex = this._findIndexOfUint8Array(this.#saveFileBytes, HEADER_B);

        if(headerIndex !== 0)
        {
            throw new Error('Invalid Save Game Format');
        }

        this.#primaryDBLocation = this._getDBByteOffsets(PRIMARY_DB_B);
        this.#secondaryDBLocation = this._getDBByteOffsets(SECONDARY_DB_B);

        const primaryDB = this._getDBByteArray(this.#primaryDBLocation);
        const secondaryDB = this._getDBByteArray(this.#secondaryDBLocation);
        this.#primaryDBBytes = primaryDB;
        this.#secondaryDBBytes = secondaryDB;
    }

    private _findIndexOfUint8Array(arrayToSearch : Uint8Array, searchArray : Uint8Array, startFrom = 0) : number
    {
        const slicedArrayToSearch = arrayToSearch.slice(startFrom);

        const foundIndex = slicedArrayToSearch.findIndex((val, index) =>
        {
            // No need to do any fancy slicing if the first values don't match, or we aren't past the offset.
            if(searchArray[0] !== val)
            {
                return false;
            }
            const compareSlice = slicedArrayToSearch.slice(index, index + searchArray.length);
            for(let i = 0; i < compareSlice.length; i++)
            {
                if(compareSlice[i] !== searchArray[i])
                {
                    return false;
                }
            }
            return true;
        });

        return (foundIndex === -1) ? -1 : foundIndex + startFrom;
    }

    private _getDBByteOffsets(startSearchBytes : Uint8Array) : DBLocation
    {
        const searchOffset = this._findIndexOfUint8Array(
            this.#saveFileBytes,
            startSearchBytes
        );

        const searchByteStringOffset = this._findIndexOfUint8Array(
            this.#saveFileBytes,
            BYTE_HEADER,
            searchOffset
        );

        return {
            sizeOffset: searchByteStringOffset + BYTE_HEADER.length + 2,
            dbOffset: searchByteStringOffset + BYTE_HEADER.length + 2 + 4
        };
    }

    private _getDBByteArray(dbLocation : DBLocation) : Uint8Array
    {
        const dbSize = this.#saveFileView.getInt32(dbLocation.sizeOffset, true);
        return this.#saveFileBytes.slice(dbLocation.dbOffset, dbLocation.dbOffset + dbSize);
    }

    // private _cleanSQLiteArtifacts(db : Uint8Array) : Uint8Array
    // {
    //     db[27] = 0;
    //     db[95] = 0;
    //     db[98] = 67;
    //     db[99] = 195;
    //     return db;
    // }

    generateSaveFile(primaryDB : Uint8Array, secondaryDB : Uint8Array | null = null) : Uint8Array
    {
        secondaryDB = secondaryDB ? secondaryDB : this.#secondaryDBBytes;

        // primaryDB = this._cleanSQLiteArtifacts(primaryDB);
        // secondaryDB = this._cleanSQLiteArtifacts(secondaryDB);

        const startSection = this.#saveFileBytes.slice(0, this.#primaryDBLocation.dbOffset);

        const middleSection = this.#saveFileBytes.slice(
            this.#primaryDBLocation.dbOffset + this.#primaryDBBytes.length,
            (this.#primaryDBLocation.dbOffset + this.#primaryDBBytes.length)
            + (this.#secondaryDBLocation.dbOffset - (this.#primaryDBLocation.dbOffset + this.#primaryDBBytes.length))
        );
        const endSection = this.#saveFileBytes.slice(this.#secondaryDBLocation.dbOffset + this.#secondaryDBBytes.length);

        const fileLength
            = startSection.length
            + primaryDB.length
            + middleSection.length
            + secondaryDB.length
            + endSection.length;

        const fileArray = new Uint8Array(fileLength);
        fileArray.set(startSection, 0);
        fileArray.set(primaryDB, startSection.length);
        fileArray.set(middleSection, startSection.length + primaryDB.length);
        fileArray.set(secondaryDB, startSection.length + primaryDB.length + middleSection.length);
        fileArray.set(endSection, startSection.length + primaryDB.length + middleSection.length + secondaryDB.length);

        const primaryDBSizeView = new DataView(fileArray.buffer, startSection.length - 4, 4);
        const primaryDBArraySizeView = new DataView(fileArray.buffer, startSection.length - 30, 4);
        const secondaryDBSizeView
            = new DataView(fileArray.buffer, startSection.length + primaryDB.length + middleSection.length - 4, 4);
        const secondaryDBArraySizeView
            = new DataView(fileArray.buffer, startSection.length + primaryDB.length + middleSection.length - 30, 4);

        primaryDBSizeView.setInt32(0, primaryDB.length, true);
        primaryDBArraySizeView.setInt32(0, primaryDB.length + 4, true);
        secondaryDBSizeView.setInt32(0, secondaryDB.length, true);
        secondaryDBArraySizeView.setInt32(0, secondaryDB.length + 4, true);

        return fileArray;
    }

    get primaryDB() : Uint8Array
    {
        return this.#primaryDBBytes;
    }

    get secondaryDB() : Uint8Array
    {
        return this.#secondaryDBBytes;
    }
}    
