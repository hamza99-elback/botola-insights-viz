import streamlit as st
from mplsoccer import Pitch
import io

def main():
    st.title('Football Pitch Visualization')
    
    # Create a mplsoccer pitch instance
    pitch = Pitch()
    fig, ax = pitch.draw(figsize=(8, 4))
    # Display the pitch
    st.pyplot(fig)
     # Save figure to a BytesIO object
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight', transparent=True)
    buf.seek(0)

    # Provide BytesIO object to download button
    st.download_button("Download file", buf, file_name='pitch.png', mime='image/png')


if __name__ == "__main__":
    main()
