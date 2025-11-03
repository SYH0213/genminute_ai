
import sqlite3
import uuid
import datetime

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_stt_to_db(self, segments, audio_filename, title):
        meeting_id = str(uuid.uuid4())
        meeting_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = self._get_connection()
        cursor = conn.cursor()
        for segment in segments:
            cursor.execute("""
                INSERT INTO meeting_dialogues 
                (meeting_id, meeting_date, speaker_label, start_time, segment, confidence, audio_file, title)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meeting_id, meeting_date, str(segment['speaker']), segment['start_time'],
                segment['text'], segment['confidence'], audio_filename, title
            ))
        conn.commit()
        conn.close()
        print(f"✅ DB 저장 완료: meeting_id={meeting_id}")
        return meeting_id

    def get_meeting_by_id(self, meeting_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meeting_dialogues WHERE meeting_id = ? ORDER BY start_time ASC", (meeting_id,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def get_all_meetings(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT meeting_id, title, MAX(meeting_date) as date 
            FROM meeting_dialogues 
            GROUP BY meeting_id 
            ORDER BY date DESC
        """)
        meetings = cursor.fetchall()
        conn.close()
        return meetings

    def get_segments_by_meeting_id(self, meeting_id):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM meeting_dialogues WHERE meeting_id = ? ORDER BY start_time ASC", (meeting_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def delete_meeting_data(self, meeting_id=None, audio_file=None, title=None):
        """
        지정된 조건에 따라 회의 데이터를 삭제합니다.
        경고: 아무 조건도 주어지지 않으면 테이블의 모든 데이터가 삭제됩니다.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "DELETE FROM meeting_dialogues"
        conditions = []
        params = []

        if meeting_id:
            conditions.append("meeting_id = ?")
            params.append(meeting_id)
        if audio_file:
            conditions.append("audio_file = ?")
            params.append(audio_file)
        if title:
            conditions.append("title = ?")
            params.append(title)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor.execute(query, tuple(params))
        deleted_rows = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"✅ DB 삭제 완료: {deleted_rows}개 행 삭제됨")
        return deleted_rows
