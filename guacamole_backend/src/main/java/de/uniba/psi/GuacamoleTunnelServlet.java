package de.uniba.psi;

import javax.servlet.http.HttpServletRequest;
import org.apache.guacamole.GuacamoleException;
import org.apache.guacamole.net.GuacamoleSocket;
import org.apache.guacamole.net.GuacamoleTunnel;
import org.apache.guacamole.net.InetGuacamoleSocket;
import org.apache.guacamole.net.SimpleGuacamoleTunnel;
import org.apache.guacamole.protocol.ConfiguredGuacamoleSocket;
import org.apache.guacamole.protocol.GuacamoleConfiguration;
import org.apache.guacamole.servlet.GuacamoleHTTPTunnelServlet;

import com.google.gson.Gson;

import java.io.IOException;

import okhttp3.HttpUrl;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;

public class GuacamoleTunnelServlet extends GuacamoleHTTPTunnelServlet {

    public static final String BACKEND_URL = "http://scanner.psi.test/api/get_vnc_port";
    public static final String CHARSET = "UTF-8";

    @Override
    protected GuacamoleTunnel doConnect(HttpServletRequest request) throws GuacamoleException {
        // get vnc port
        String session_id = request.getParameter("session");
        int vnc_port = getVNCPort(session_id);
        // config
        GuacamoleConfiguration config = new GuacamoleConfiguration();
        config.setProtocol("vnc");
        config.setParameter("hostname", "localhost");
        config.setParameter("port", String.valueOf(vnc_port));
        config.setParameter("password", "asdf");

        // Connect to guacd
        GuacamoleSocket socket = new ConfiguredGuacamoleSocket(new InetGuacamoleSocket("localhost", 4822), config);

        // Return a new tunnel which uses the connected socket
        return new SimpleGuacamoleTunnel(socket);
    }

    private int getVNCPort(String session_id) throws GuacamoleException {
        OkHttpClient client = new OkHttpClient();
        HttpUrl url = HttpUrl.parse(BACKEND_URL)
                .newBuilder()
                .addQueryParameter("session_id", session_id)
                .build();

        Request request = new Request.Builder()
                .url(url)
                .build();

        try (Response response = client.newCall(request).execute()) {
            if (response.isSuccessful()) {
                VNCResult vnc = new Gson().fromJson(response.body().string(), VNCResult.class);
                return vnc.vnc_port;
            } else {
                throw new GuacamoleException("message");
            }
        } catch (IOException e) {
            throw new GuacamoleException("Session could not be retrieved from Backend. IO", e);
        }
    }

}
